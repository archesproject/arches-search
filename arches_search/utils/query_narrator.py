from dataclasses import dataclass

from django.conf import settings
from django.utils import translation
from django.utils.translation import get_language, gettext as _

from arches.app.models import models as arches_models

from arches_search.models.models import AdvancedSearchFacet
from arches_search.utils.node_alias_metadata import (
    build_node_alias_metadata_for_payload_query,
)
from arches_search.utils.resource_names_for_payload import (
    build_resource_names_for_payload,
)


_RTL_LOCALES = frozenset({"ar", "he", "ur", "fa", "yi"})


@dataclass(frozen=True)
class NarrationContext:
    graph_names: dict  # slug → display name
    node_labels: dict  # (graph_slug, node_alias) → widget label
    node_datatypes: dict  # (graph_slug, node_alias) → datatype name
    operator_labels: dict  # operator token → prose label
    resource_names: dict  # resource UUID → display name
    is_rtl: bool


def narrate_query(payload: dict, language_code: str | None = None) -> str:
    if not payload.get("graph_slug"):
        return ""
    active_language = language_code or get_language() or settings.LANGUAGE_CODE
    with translation.override(active_language):
        ctx = _build_context(payload, active_language)
        lines = _describe_group(payload, ctx, depth=0)
        return _render(payload, lines, ctx)


def _build_context(payload: dict, language_code: str) -> NarrationContext:
    node_meta = build_node_alias_metadata_for_payload_query(payload)
    resource_names = build_resource_names_for_payload(payload)
    graph_names = {
        str(graph.slug): str(graph.name)
        for graph in arches_models.GraphModel.objects.filter(
            slug__in=_collect_graph_slugs(payload)
        )
    }
    operator_labels = {
        facet.operator: label
        for facet in AdvancedSearchFacet.objects.all()
        if facet.operator and (label := str(facet.label))
    }
    return NarrationContext(
        graph_names=graph_names,
        node_labels={
            key: meta["card_x_node_x_widget_label"] for key, meta in node_meta.items()
        },
        node_datatypes={key: meta["datatype"] for key, meta in node_meta.items()},
        operator_labels=operator_labels,
        resource_names=resource_names,
        is_rtl=language_code.split("-")[0].lower() in _RTL_LOCALES,
    )


def _collect_graph_slugs(payload: dict) -> set:
    slugs = set()

    def add(slug):
        if slug:
            slugs.add(slug)

    add(payload.get("graph_slug"))
    for clause in payload.get("clauses", []):
        add(clause.get("subject", {}).get("graph_slug"))
        for operand in clause.get("operands", []):
            if operand.get("type") == "PATH":
                path = operand.get("value") or []
                if path and isinstance(path[-1], list) and path[-1]:
                    add(path[-1][0])
    add((payload.get("relationship") or {}).get("path", {}).get("graph_slug"))
    for subgroup in payload.get("groups", []):
        slugs.update(_collect_graph_slugs(subgroup))
    return slugs


def _render(payload: dict, lines: list, ctx: NarrationContext) -> str:
    graph_slug = payload["graph_slug"]
    graph_label = ctx.graph_names.get(graph_slug, graph_slug)
    if not lines:
        # Translators: e.g. 'All "Heritage Site" records.'
        return _('All "%(graph)s" records.') % {"graph": graph_label}
    # Translators: e.g. 'All "Heritage Site" records where:'
    intro = _('All "%(graph)s" records where:') % {"graph": graph_label}
    return intro + "\n" + "\n".join(lines)


def _indent_prefix(depth: int, is_rtl: bool) -> str:
    # U+200F anchors bidi base direction so the bullet renders at the right edge in RTL.
    return ("‏" if is_rtl else "") + "  " * depth + "• "


def _describe_group(group: dict, ctx: NarrationContext, depth: int) -> list:
    logic = group.get("logic", "AND")
    result = []

    clause_phrases = [
        phrase
        for clause in group.get("clauses", [])
        if (phrase := _describe_clause(clause, ctx))
    ]
    for index, phrase in enumerate(clause_phrases):
        prefix = _indent_prefix(depth, ctx.is_rtl)
        if logic == "OR" and index > 0:
            # Translators: e.g. 'OR: "Name" equals "Temple"'
            result.append(prefix + _("OR: %(condition)s") % {"condition": phrase})
        else:
            result.append(prefix + phrase)

    relationship = group.get("relationship") or {}
    subgroups = group.get("groups", [])
    rel_path = relationship.get("path", {})

    if rel_path.get("graph_slug") and rel_path.get("node_alias"):
        inner_group = subgroups[0] if subgroups else None
        linked_graph_slug = inner_group.get("graph_slug", "") if inner_group else ""
        rel_phrase = _describe_relationship(relationship, linked_graph_slug, ctx)

        if rel_phrase:
            prefix = _indent_prefix(depth, ctx.is_rtl)
            inner_lines = (
                _describe_group(inner_group, ctx, depth + 1) if inner_group else []
            )
            full_phrase = rel_phrase + (":" if inner_lines else "")
            if logic == "OR" and clause_phrases:
                result.append(
                    prefix + _("OR: %(condition)s") % {"condition": full_phrase}
                )
            else:
                result.append(prefix + full_phrase)
            result.extend(inner_lines)

        for subgroup in subgroups[1:]:
            result.extend(_describe_group(subgroup, ctx, depth))
    else:
        for subgroup in subgroups:
            result.extend(_describe_group(subgroup, ctx, depth))

    return result


def _describe_clause(clause: dict, ctx: NarrationContext) -> str:
    field_label = _resolve_clause_field_label(clause, ctx)
    operator = clause.get("operator", "")
    if not field_label or not operator:
        return ""

    operator_label = ctx.operator_labels.get(operator, operator)
    subject = clause.get("subject", {})
    datatype = ""
    if subject.get("type") == "NODE":
        datatype = ctx.node_datatypes.get(
            (subject.get("graph_slug"), subject.get("node_alias")), ""
        )

    value_phrase = _format_value_list(
        [
            description
            for operand in clause.get("operands", [])
            if (description := _describe_operand(operand, datatype, ctx))
        ]
    )

    if value_phrase:
        # Translators: e.g. '"Name" equals "Acropolis"'
        return _('"%(field)s" %(operator)s %(value)s') % {
            "field": field_label,
            "operator": operator_label,
            "value": value_phrase,
        }
    # Translators: e.g. '"Status" has any value'
    return _('"%(field)s" %(operator)s') % {
        "field": field_label,
        "operator": operator_label,
    }


def _resolve_clause_field_label(clause: dict, ctx: NarrationContext) -> str:
    subject = clause.get("subject", {})
    graph_slug = subject.get("graph_slug")
    if not graph_slug:
        return ""

    if subject.get("type") == "NODE":
        node_alias = subject.get("node_alias")
        if node_alias:
            return ctx.node_labels.get((graph_slug, node_alias), "") or node_alias

    if subject.get("type") == "SEARCH_MODELS" and subject.get("search_models"):
        graph_label = ctx.graph_names.get(graph_slug, graph_slug)
        if graph_label:
            # Translators: e.g. 'any field in "Heritage Site"'
            return _('any field in "%(graph)s"') % {"graph": graph_label}
        return _("any field")

    return ""


def _describe_operand(
    operand: dict, subject_datatype: str, ctx: NarrationContext
) -> str:
    if operand.get("type") == "PATH":
        return _describe_path_value(operand.get("value"), ctx)

    raw = operand.get("display_value")
    if raw is None:
        raw = operand.get("value")
    if raw is None:
        return ""

    if isinstance(raw, list):
        return _format_value_list(
            [
                f'"{ctx.resource_names.get(item, item)}"'
                for item in raw
                if isinstance(item, str)
            ]
        )

    if subject_datatype == "string" and isinstance(raw, dict) and len(raw) == 1:
        # Localized string value: {lang_code: text}
        ((language_code, text),) = raw.items()
        if not isinstance(text, str) or not text.strip():
            return ""
        text = text.strip()
        language_code = language_code.strip()
        if language_code:
            # Translators: e.g. '"Temple" (en)'
            return _('"%(value)s" (%(language)s)') % {
                "value": text,
                "language": language_code,
            }
        return f'"{text}"'

    # bool must be checked before int: isinstance(True, int) is True
    if isinstance(raw, bool):
        return "true" if raw else "false"
    if isinstance(raw, (int, float)):
        return str(raw)
    text = str(raw).strip()
    return f'"{text}"' if text else ""


def _describe_path_value(value, ctx: NarrationContext) -> str:
    if not isinstance(value, list) or not value:
        return ""
    last_entry = value[-1]
    if not isinstance(last_entry, list) or len(last_entry) < 2:
        return ""

    path_graph_slug, path_node_alias = str(last_entry[0]), str(last_entry[1])
    graph_label = ctx.graph_names.get(path_graph_slug, path_graph_slug)
    field_label = (
        ctx.node_labels.get((path_graph_slug, path_node_alias), "") or path_node_alias
    )

    if graph_label and field_label:
        # Translators: e.g. 'the "Name" field in "Heritage Site"'
        return _('the "%(field)s" field in "%(graph)s"') % {
            "field": field_label,
            "graph": graph_label,
        }
    if graph_label:
        return f'"{graph_label}"'
    if field_label:
        # Translators: e.g. 'the "Name" field'
        return _('the "%(field)s" field') % {"field": field_label}
    return ""


def _format_value_list(values: list) -> str:
    non_empty = [v for v in values if v]
    if not non_empty:
        return ""
    if len(non_empty) == 1:
        return non_empty[0]
    if len(non_empty) == 2:
        # Translators: two values, e.g. '"Temple" and "Acropolis"'
        return _("%(first)s and %(second)s") % {
            "first": non_empty[0],
            "second": non_empty[1],
        }
    # Translators: Oxford-comma list, e.g. '"Temple", "Acropolis", and "Parthenon"'
    return _("%(items)s, and %(last)s") % {
        "items": ", ".join(non_empty[:-1]),
        "last": non_empty[-1],
    }


def _describe_relationship(
    relationship: dict, linked_graph_slug: str, ctx: NarrationContext
) -> str:
    path = relationship.get("path", {})
    graph_slug = path.get("graph_slug")  # source graph, used for field label
    node_alias = path.get("node_alias")
    if not graph_slug or not node_alias:
        return ""

    params = {
        "graph": ctx.graph_names.get(linked_graph_slug, linked_graph_slug),
        "field": ctx.node_labels.get((graph_slug, node_alias), "") or node_alias,
    }
    is_inverse = relationship.get("is_inverse", False)
    quantifier = relationship.get("traversal_quantifier", "ANY")
    if quantifier not in ("ALL", "NONE"):
        quantifier = "ANY"

    if not is_inverse:
        if quantifier == "ALL":
            # Translators: e.g. 'where all linked "Activity" records (via "related site") match'
            return (
                _('where all linked "%(graph)s" records (via "%(field)s") match')
                % params
            )
        if quantifier == "NONE":
            # Translators: e.g. 'with no linked "Activity" records (via "related site")'
            return _('with no linked "%(graph)s" records (via "%(field)s")') % params
        # Translators: e.g. 'with at least one linked "Activity" (via "related site")'
        return _('with at least one linked "%(graph)s" (via "%(field)s")') % params

    if quantifier == "ALL":
        # Translators: e.g. 'referenced by all "Monument" records (via "mentioned site")'
        return _('referenced by all "%(graph)s" records (via "%(field)s")') % params
    if quantifier == "NONE":
        # Translators: e.g. 'not referenced by any "Monument" (via "mentioned site")'
        return _('not referenced by any "%(graph)s" (via "%(field)s")') % params
    # Translators: e.g. 'referenced by at least one "Monument" (via "mentioned site")'
    return _('referenced by at least one "%(graph)s" (via "%(field)s")') % params
