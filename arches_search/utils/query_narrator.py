from dataclasses import dataclass

from django.conf import settings
from django.utils import translation
from django.utils.translation import get_language, get_language_bidi, gettext as _

from arches.app.models import models as arches_models

from arches_search.models.models import AdvancedSearchFacet
from arches_search.utils.node_alias_metadata import (
    build_node_alias_metadata_for_payload_query,
)
from arches_search.utils.resource_names_for_payload import (
    build_resource_names_for_payload,
)


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
        context = _build_context(payload)
        lines = _describe_group(payload, context, 0)
        return _render(payload, lines, context)


def _build_context(payload: dict) -> NarrationContext:
    node_metadata = build_node_alias_metadata_for_payload_query(payload)
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
            alias_key: alias_metadata["card_x_node_x_widget_label"]
            for alias_key, alias_metadata in node_metadata.items()
        },
        node_datatypes={
            alias_key: alias_metadata["datatype"]
            for alias_key, alias_metadata in node_metadata.items()
        },
        operator_labels=operator_labels,
        resource_names=resource_names,
        is_rtl=get_language_bidi(),
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


def _render(payload: dict, lines: list, context: NarrationContext) -> str:
    graph_slug = payload["graph_slug"]
    graph_label = context.graph_names.get(graph_slug, graph_slug)
    if not lines:
        return _('All "%(graph)s" records.') % {"graph": graph_label}
    intro = _('All "%(graph)s" records where:') % {"graph": graph_label}
    return intro + "\n" + "\n".join(lines)


def _indent_prefix(depth: int, is_rtl: bool) -> str:
    # U+200F anchors bidi base direction so the bullet renders at the right edge in RTL.
    return ("‏" if is_rtl else "") + "  " * depth + "• "


def _describe_group(group: dict, context: NarrationContext, depth: int) -> list:
    logic = group.get("logic", "AND")
    prefix = _indent_prefix(depth, context.is_rtl)
    result = []

    clause_phrases = [
        phrase
        for clause in group.get("clauses", [])
        if (phrase := _describe_clause(clause, context))
    ]
    for index, phrase in enumerate(clause_phrases):
        if logic == "OR" and index > 0:
            result.append(prefix + _("OR: %(condition)s") % {"condition": phrase})
        else:
            result.append(prefix + phrase)

    relationship = group.get("relationship") or {}
    subgroups = group.get("groups", [])
    relationship_path = relationship.get("path", {})

    if relationship_path.get("graph_slug") and relationship_path.get("node_alias"):
        inner_group = subgroups[0] if subgroups else None
        linked_graph_slug = inner_group.get("graph_slug", "") if inner_group else ""
        relationship_phrase = _describe_relationship(
            relationship, linked_graph_slug, context
        )

        if relationship_phrase:
            inner_lines = (
                _describe_group(inner_group, context, depth + 1) if inner_group else []
            )
            full_phrase = relationship_phrase + (":" if inner_lines else "")
            if logic == "OR" and clause_phrases:
                result.append(
                    prefix + _("OR: %(condition)s") % {"condition": full_phrase}
                )
            else:
                result.append(prefix + full_phrase)
            result.extend(inner_lines)

        for subgroup in subgroups[1:]:
            result.extend(_describe_group(subgroup, context, depth))
    else:
        for subgroup in subgroups:
            result.extend(_describe_group(subgroup, context, depth))

    return result


def _describe_clause(clause: dict, context: NarrationContext) -> str:
    field_label = _resolve_clause_field_label(clause, context)
    operator = clause.get("operator", "")
    if not field_label or not operator:
        return ""

    operator_label = context.operator_labels.get(operator, operator)
    subject = clause.get("subject", {})
    datatype = ""
    if subject.get("type") == "NODE":
        datatype = context.node_datatypes.get(
            (subject.get("graph_slug"), subject.get("node_alias")), ""
        )

    value_phrase = _format_value_list(
        [
            operand_description
            for operand in clause.get("operands", [])
            if (operand_description := _describe_operand(operand, datatype, context))
        ]
    )

    if value_phrase:
        return _('"%(field)s" %(operator)s %(value)s') % {
            "field": field_label,
            "operator": operator_label,
            "value": value_phrase,
        }
    return _('"%(field)s" %(operator)s') % {
        "field": field_label,
        "operator": operator_label,
    }


def _resolve_clause_field_label(clause: dict, context: NarrationContext) -> str:
    subject = clause.get("subject", {})
    subject_type = subject.get("type")
    graph_slug = subject.get("graph_slug")
    if not graph_slug:
        return ""

    if subject_type == "NODE":
        node_alias = subject.get("node_alias")
        if node_alias:
            return context.node_labels.get((graph_slug, node_alias), "") or node_alias

    if subject_type == "SEARCH_MODELS" and subject.get("search_models"):
        graph_label = context.graph_names.get(graph_slug, graph_slug)
        return (
            _('any field in "%(graph)s"') % {"graph": graph_label}
            if graph_label
            else _("any field")
        )

    return ""


def _describe_operand(
    operand: dict, subject_datatype: str, context: NarrationContext
) -> str:
    if operand.get("type") == "PATH":
        return _describe_path_value(operand.get("value"), context)

    raw_value = operand.get("display_value")
    if raw_value is None:
        raw_value = operand.get("value")
    if raw_value is None:
        return ""

    if isinstance(raw_value, list):
        return _format_value_list(
            [
                f'"{context.resource_names.get(item, item)}"'
                for item in raw_value
                if isinstance(item, str)
            ]
        )

    if (
        subject_datatype == "string"
        and isinstance(raw_value, dict)
        and len(raw_value) == 1
    ):
        # Localized string value: {lang_code: text}
        ((language_code, text),) = raw_value.items()
        if not isinstance(text, str) or not text.strip():
            return ""
        text = text.strip()
        if language_code:
            return _('"%(value)s" (%(language)s)') % {
                "value": text,
                "language": language_code,
            }
        return f'"{text}"'

    # bool must be checked before int: isinstance(True, int) is True
    if isinstance(raw_value, bool):
        return "true" if raw_value else "false"
    if isinstance(raw_value, (int, float)):
        return str(raw_value)
    text = str(raw_value).strip()
    return f'"{text}"' if text else ""


def _describe_path_value(path_value, context: NarrationContext) -> str:
    if not isinstance(path_value, list) or not path_value:
        return ""
    last_entry = path_value[-1]
    if not isinstance(last_entry, list) or len(last_entry) < 2:
        return ""

    path_graph_slug, path_node_alias = last_entry[0], last_entry[1]
    graph_label = context.graph_names.get(path_graph_slug, path_graph_slug)
    field_label = (
        context.node_labels.get((path_graph_slug, path_node_alias), "")
        or path_node_alias
    )

    if graph_label and field_label:
        return _('the "%(field)s" field in "%(graph)s"') % {
            "field": field_label,
            "graph": graph_label,
        }
    if graph_label:
        return f'"{graph_label}"'
    if field_label:
        return _('the "%(field)s" field') % {"field": field_label}
    return ""


def _format_value_list(values: list) -> str:
    non_empty = [value for value in values if value]
    if not non_empty:
        return ""
    if len(non_empty) == 1:
        return non_empty[0]
    if len(non_empty) == 2:
        return _("%(first)s and %(second)s") % {
            "first": non_empty[0],
            "second": non_empty[1],
        }
    return _("%(items)s, and %(last)s") % {
        "items": ", ".join(non_empty[:-1]),
        "last": non_empty[-1],
    }


def _describe_relationship(
    relationship: dict, linked_graph_slug: str, context: NarrationContext
) -> str:
    relationship_path = relationship.get("path", {})
    source_graph_slug = relationship_path.get(
        "graph_slug"
    )  # source graph, used for field label lookup
    node_alias = relationship_path.get("node_alias")

    template_params = {
        "graph": context.graph_names.get(linked_graph_slug, linked_graph_slug),
        "field": context.node_labels.get((source_graph_slug, node_alias), "")
        or node_alias,
    }
    is_inverse = relationship.get("is_inverse", False)
    quantifier = relationship.get("traversal_quantifier", "ANY")
    if quantifier not in ("ALL", "NONE"):
        quantifier = "ANY"

    if not is_inverse:
        if quantifier == "ALL":
            return (
                _('where all linked "%(graph)s" records (via "%(field)s") match')
                % template_params
            )
        if quantifier == "NONE":
            return (
                _('with no linked "%(graph)s" records (via "%(field)s")')
                % template_params
            )
        return (
            _('with at least one linked "%(graph)s" (via "%(field)s")')
            % template_params
        )

    if quantifier == "ALL":
        return (
            _('referenced by all "%(graph)s" records (via "%(field)s")')
            % template_params
        )
    if quantifier == "NONE":
        return (
            _('not referenced by any "%(graph)s" (via "%(field)s")') % template_params
        )
    return (
        _('referenced by at least one "%(graph)s" (via "%(field)s")') % template_params
    )
