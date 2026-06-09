from dataclasses import dataclass
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext as _

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
    if not (payload or {}).get("graph_slug"):
        return ""
    effective_language = language_code or _get_language() or settings.LANGUAGE_CODE
    with translation.override(effective_language):
        ctx = _build_context(payload, effective_language)
        lines = _describe_group(payload, ctx, depth=0)
        return _render(payload, lines, ctx)


def _get_language():
    from django.utils.translation import get_language

    return get_language()


def _build_context(payload: dict, language_code: str) -> NarrationContext:
    node_meta = build_node_alias_metadata_for_payload_query(payload)
    resource_names = build_resource_names_for_payload(payload)

    slugs = _collect_graph_slugs(payload)
    graph_names = {
        str(graph.slug): str(graph.name)
        for graph in arches_models.GraphModel.objects.filter(slug__in=slugs)
    }

    operator_labels = {
        facet.operator: str(facet.label)
        for facet in AdvancedSearchFacet.objects.all()
        if facet.operator and str(facet.label)
    }

    base_lang = language_code.split("-")[0].lower() if language_code else ""
    return NarrationContext(
        graph_names=graph_names,
        node_labels={
            key: meta["card_x_node_x_widget_label"] for key, meta in node_meta.items()
        },
        node_datatypes={key: meta["datatype"] for key, meta in node_meta.items()},
        operator_labels=operator_labels,
        resource_names=resource_names,
        is_rtl=base_lang in _RTL_LOCALES,
    )


def _collect_graph_slugs(payload: dict) -> set:
    slugs = set()

    slug = (payload.get("graph_slug") or "").strip()
    if slug:
        slugs.add(slug)

    for clause in payload.get("clauses", []):
        subject_slug = (clause.get("subject", {}).get("graph_slug") or "").strip()
        if subject_slug:
            slugs.add(subject_slug)
        for operand in clause.get("operands", []):
            if operand.get("type") == "PATH":
                value = operand.get("value")
                if isinstance(value, list) and value:
                    last_entry = value[-1]
                    if isinstance(last_entry, list) and last_entry:
                        path_slug = str(last_entry[0]).strip()
                        if path_slug:
                            slugs.add(path_slug)

    relationship = payload.get("relationship") or {}
    rel_slug = (relationship.get("path", {}).get("graph_slug") or "").strip()
    if rel_slug:
        slugs.add(rel_slug)

    for subgroup in payload.get("groups", []):
        slugs.update(_collect_graph_slugs(subgroup))

    return slugs


def _render(payload: dict, lines: list, ctx: NarrationContext) -> str:
    graph_slug = payload.get("graph_slug", "")
    graph_label = ctx.graph_names.get(graph_slug, graph_slug)

    if not lines:
        # Translators: e.g. 'All "Heritage Site" records.'
        return _('All "%(graph)s" records.') % {"graph": graph_label}

    # Translators: e.g. 'All "Heritage Site" records where:'
    intro = _('All "%(graph)s" records where:') % {"graph": graph_label}
    return intro + "\n" + "\n".join(lines)


def _indent_prefix(depth: int, is_rtl: bool) -> str:
    # U+200F anchors bidi base direction so the bullet renders at the right edge in RTL.
    rtl_mark = "‏" if is_rtl else ""
    return rtl_mark + "  " * depth + "• "


def _describe_group(group: dict, ctx: NarrationContext, depth: int) -> list:
    logic = group.get("logic", "AND")
    result = []

    clause_phrases = []
    for clause in group.get("clauses", []):
        phrase = _describe_clause(clause, ctx)
        if phrase:
            clause_phrases.append(phrase)

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
    has_relationship = bool(
        rel_path.get("graph_slug", "").strip()
        and rel_path.get("node_alias", "").strip()
    )

    if has_relationship:
        inner_group = subgroups[0] if subgroups else None
        linked_graph_slug = (
            (inner_group.get("graph_slug") or "").strip() if inner_group else ""
        )
        rel_phrase = _describe_relationship(relationship, linked_graph_slug, ctx)
        remaining_groups = subgroups[1:]

        if rel_phrase:
            prefix = _indent_prefix(depth, ctx.is_rtl)
            has_prior = bool(clause_phrases)
            inner_lines = (
                _describe_group(inner_group, ctx, depth + 1) if inner_group else []
            )
            full_phrase = rel_phrase + (":" if inner_lines else "")

            if logic == "OR" and has_prior:
                result.append(
                    prefix + _("OR: %(condition)s") % {"condition": full_phrase}
                )
            else:
                result.append(prefix + full_phrase)

            result.extend(inner_lines)

        for nested_group in remaining_groups:
            result.extend(_describe_group(nested_group, ctx, depth))
    else:
        for nested_group in subgroups:
            result.extend(_describe_group(nested_group, ctx, depth))

    return result


def _describe_clause(clause: dict, ctx: NarrationContext) -> str:
    subject = clause.get("subject", {})
    subject_graph_slug = (subject.get("graph_slug") or "").strip()
    if not subject_graph_slug:
        return ""

    field_label = _resolve_clause_field_label(clause, ctx)
    if not field_label:
        return ""

    raw_operator = (clause.get("operator") or "").strip()
    if not raw_operator:
        return ""
    operator_label = ctx.operator_labels.get(raw_operator, raw_operator).strip()
    if not operator_label:
        return ""

    subject_node_alias = (
        (subject.get("node_alias") or "").strip()
        if subject.get("type") == "NODE"
        else ""
    )
    subject_datatype = (
        ctx.node_datatypes.get((subject_graph_slug, subject_node_alias), "")
        if subject_node_alias
        else ""
    )

    operand_descriptions = []
    for operand in clause.get("operands", []):
        desc = _describe_operand(operand, subject_datatype, ctx)
        if desc:
            operand_descriptions.append(desc)

    value_phrase = _format_value_list(operand_descriptions).strip()

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
    subject_type = subject.get("type", "")
    subject_graph_slug = (subject.get("graph_slug") or "").strip()

    if not subject_graph_slug:
        return ""

    if subject_type == "NODE":
        node_alias = (subject.get("node_alias") or "").strip()
        if node_alias:
            label = ctx.node_labels.get((subject_graph_slug, node_alias), "").strip()
            return label or node_alias

    if subject_type == "SEARCH_MODELS" and subject.get("search_models"):
        graph_label = ctx.graph_names.get(
            subject_graph_slug, subject_graph_slug
        ).strip()
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

    raw_value = operand.get("display_value")
    if raw_value is None:
        raw_value = operand.get("value")

    if raw_value is None:
        return ""

    if isinstance(raw_value, list):
        resolved = []
        for item in raw_value:
            if isinstance(item, str):
                name = ctx.resource_names.get(item, item)
                resolved.append(f'"{name}"')
        return _format_value_list(resolved)

    if (
        subject_datatype == "string"
        and isinstance(raw_value, dict)
        and len(raw_value) == 1
    ):
        # Localized string value: {language_code: text}
        language_code, localized_value = next(iter(raw_value.items()))
        if isinstance(localized_value, str):
            trimmed_value = localized_value.strip()
            trimmed_lang = language_code.strip()
            if trimmed_value and trimmed_lang:
                # Translators: e.g. '"Temple" (en)'
                return _('"%(value)s" (%(language)s)') % {
                    "value": trimmed_value,
                    "language": trimmed_lang,
                }
            if trimmed_value:
                return f'"{trimmed_value}"'
        return ""

    # bool check must precede int because isinstance(True, int) is True in Python
    if isinstance(raw_value, bool):
        return "true" if raw_value else "false"

    if isinstance(raw_value, (int, float)):
        return str(raw_value)

    text = str(raw_value).strip()
    return f'"{text}"' if text else ""


def _describe_path_value(value, ctx: NarrationContext) -> str:
    if not isinstance(value, list) or not value:
        return ""

    last_entry = value[-1]
    if not isinstance(last_entry, list) or len(last_entry) < 2:
        return ""

    path_graph_slug = str(last_entry[0]).strip()
    path_node_alias = str(last_entry[1]).strip()
    path_graph_label = ctx.graph_names.get(path_graph_slug, path_graph_slug).strip()
    path_field_label = (
        ctx.node_labels.get((path_graph_slug, path_node_alias), "").strip()
        or path_node_alias
    )

    if path_graph_label and path_field_label:
        # Translators: e.g. 'the "Name" field in "Heritage Site"'
        return _('the "%(field)s" field in "%(graph)s"') % {
            "field": path_field_label,
            "graph": path_graph_label,
        }
    if path_graph_label:
        return f'"{path_graph_label}"'
    if path_field_label:
        # Translators: e.g. 'the "Name" field'
        return _('the "%(field)s" field') % {"field": path_field_label}
    return ""


def _format_value_list(values: list) -> str:
    non_empty = [v.strip() for v in values if v.strip()]
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
    graph_slug = (
        path.get("graph_slug") or ""
    ).strip()  # source graph, used for field label
    node_alias = (path.get("node_alias") or "").strip()

    if not graph_slug or not node_alias:
        return ""

    graph_label = ctx.graph_names.get(linked_graph_slug, linked_graph_slug)
    field_label = (
        ctx.node_labels.get((graph_slug, node_alias), "").strip() or node_alias
    )

    is_inverse = relationship.get("is_inverse", False)
    quantifier = relationship.get("traversal_quantifier", "ANY")
    if quantifier not in ("ALL", "NONE"):
        quantifier = "ANY"

    params = {"graph": graph_label, "field": field_label}

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
