"""
Backend query narrator: converts a GroupPayload dict to a human-readable,
structured-line description in the active (or specified) language.

Output format uses bullet-indented lines rather than a composed run-on sentence.
This avoids the grammatical embedding problem — each line is a complete,
independently translatable phrase — while remaining readable for complex queries.

i18n design:
  - All name parameters (%(graph)s, %(field)s, %(value)s) are quoted in templates.
    Quoted terms are treated as opaque citation-form labels in every language;
    they are never inflected. Translators may substitute their language's native
    quote characters (« », 「 」, „ ", etc.).
  - %(operator)s is a pre-translated prose string from facet_label_cache — not quoted.
  - Every _() call has a Translators: comment that appears verbatim as #. in .po files.
  - RTL locales (ar, he, ur, fa, yi) receive a U+200F RIGHT-TO-LEFT MARK before
    each bullet to anchor bidi base direction correctly.
"""

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
    graph_names: dict  # slug → display name in active language
    node_labels: dict  # (graph_slug, node_alias) → widget label
    node_datatypes: dict  # (graph_slug, node_alias) → datatype name
    operator_labels: dict  # operator token → prose label in active language
    resource_names: dict  # resource UUID string → display name
    is_rtl: bool  # True for right-to-left locales


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def narrate_query(payload: dict, language_code: str | None = None) -> str:
    """
    Convert a GroupPayload dict to a human-readable structured-line description.

    language_code: if None, uses get_language() (already set by LocaleMiddleware
    in request context). Pass explicitly for Celery, batch exports, and tests
    where no request is active.

    translation.override() activates the target language for all _() calls and
    I18n_TextField resolutions in the call stack. In a normal Django request,
    LocaleMiddleware has already called activate(lang), so this is a no-op for
    that language — but it ensures correctness in all other contexts too.
    """
    if not (payload or {}).get("graph_slug"):
        return ""
    effective_language = language_code or _get_language() or settings.LANGUAGE_CODE
    with translation.override(effective_language):
        ctx = _build_context(payload, effective_language)
        lines = _describe_group(payload, ctx, depth=0)
        return _render(payload, lines, ctx)


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------


def _get_language():
    from django.utils.translation import get_language

    return get_language()


def _build_context(payload: dict, language_code: str) -> NarrationContext:
    """Executes all DB queries needed for narration in batched calls."""
    # These two utilities already use get_language() internally and will
    # resolve correctly because we're inside translation.override().
    node_meta = build_node_alias_metadata_for_payload_query(payload)
    resource_names = build_resource_names_for_payload(payload)

    # Batch graph name lookup — only slugs present in this payload tree.
    # _collect_graph_slugs traverses all locations where a graph_slug can appear:
    # root, clause subjects, relationship paths, PATH operand values, nested groups.
    slugs = _collect_graph_slugs(payload)
    graph_names = {
        str(graph.slug): str(graph.name)  # I18n_TextField.__str__() uses get_language()
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
    """
    Walk the full payload tree and collect every graph_slug value.
    Covers: root, clause subjects, relationship paths, PATH operand values, groups.
    """
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


# ---------------------------------------------------------------------------
# Top-level rendering
# ---------------------------------------------------------------------------


def _render(payload: dict, lines: list, ctx: NarrationContext) -> str:
    graph_slug = payload.get("graph_slug", "")
    graph_label = ctx.graph_names.get(graph_slug, graph_slug)

    if not lines:
        # Translators: Narration for a query with no filter conditions.
        # "%(graph)s" is the resource type display name (a quoted label, e.g. "Heritage Site").
        # Keep the double-quote characters — you may replace them with your language's
        # native quotation marks (e.g. « », 「 」, „ ").
        # Translate "records" to the generic word for database records in your language.
        return _('All "%(graph)s" records.') % {"graph": graph_label}

    # Translators: Opening line of a query narration; filter conditions follow on the lines below.
    # "%(graph)s" is the resource type display name (quoted label). Keep the quotes.
    intro = _('All "%(graph)s" records where:') % {"graph": graph_label}
    return intro + "\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Group description (recursive)
# ---------------------------------------------------------------------------


def _indent_prefix(depth: int, is_rtl: bool) -> str:
    # U+200F RIGHT-TO-LEFT MARK anchors bidi base direction in RTL contexts so
    # that the LTR bullet character renders at the visually correct (right) edge.
    rtl_mark = "‏" if is_rtl else ""
    return rtl_mark + "  " * depth + "• "


def _describe_group(group: dict, ctx: NarrationContext, depth: int) -> list:
    """
    Returns a flat list of fully-indented lines describing all conditions
    in this group and its descendants.

    Clauses at this level get the depth-level bullet prefix, with "OR: " added
    for items after the first when the group's logic is OR.

    Relationship descriptions get the same treatment; their inner conditions
    (groups[0]) are recursed one level deeper and appear as indented children.

    Remaining sub-groups (groups[1:] after a relationship, or all groups when
    there is no relationship) are recursed at the same depth and their lines
    appended verbatim — they already carry their own bullet prefixes.
    """
    logic = group.get("logic", "AND")
    result = []

    # Collect clause phrases first
    clause_phrases = []
    for clause in group.get("clauses", []):
        phrase = _describe_clause(clause, ctx)
        if phrase:
            clause_phrases.append(phrase)

    # Emit clause lines with logic-aware prefix
    for index, phrase in enumerate(clause_phrases):
        prefix = _indent_prefix(depth, ctx.is_rtl)
        if logic == "OR" and index > 0:
            # Translators: Prefix for a condition that belongs to an OR group.
            # %(condition)s is the full condition phrase, e.g. '"Name" equals "Temple"'.
            result.append(prefix + _("OR: %(condition)s") % {"condition": phrase})
        else:
            result.append(prefix + phrase)

    # Handle relationship + sub-groups
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

            # Trailing colon signals that indented sub-conditions follow
            suffix = ":" if inner_lines else ""
            full_phrase = rel_phrase + suffix

            if logic == "OR" and has_prior:
                # Translators: Prefix for a relationship condition in an OR group.
                # %(condition)s is the relationship phrase (may end with ":").
                result.append(
                    prefix + _("OR: %(condition)s") % {"condition": full_phrase}
                )
            else:
                result.append(prefix + full_phrase)

            result.extend(inner_lines)

        # Remaining sub-groups are siblings at this level
        for nested_group in remaining_groups:
            result.extend(_describe_group(nested_group, ctx, depth))
    else:
        for nested_group in subgroups:
            result.extend(_describe_group(nested_group, ctx, depth))

    return result


# ---------------------------------------------------------------------------
# Clause description
# ---------------------------------------------------------------------------


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
        # Translators: One search condition.
        # "%(field)s" is the field display name (quoted label — keep the quotes,
        #   you may use your language's native quote characters instead).
        # %(operator)s is a prose predicate ("equals", "is after", etc.). Do NOT quote it.
        # %(value)s is the value expression (individual values inside are already quoted).
        # Example: '"Name" equals "Acropolis"'
        return _('"%(field)s" %(operator)s %(value)s') % {
            "field": field_label,
            "operator": operator_label,
            "value": value_phrase,
        }

    # Translators: Search condition with no value (zero-arity operator).
    # "%(field)s" is the field display name (quoted label). %(operator)s is the predicate.
    # Example: '"Status" has any value'
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
            # Translators: Subject label when a clause searches across all fields of a resource type.
            # "%(graph)s" is the resource type name (quoted label). Keep the quotes.
            # Example: 'any field in "Heritage Site"'
            return _('any field in "%(graph)s"') % {"graph": graph_label}
        # Translators: Subject label when searching across all fields with no identified graph.
        return _("any field")

    return ""


# ---------------------------------------------------------------------------
# Operand description
# ---------------------------------------------------------------------------


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
        # List of UUIDs or values — resolve resource names and quote each
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
        # Localized string: {language_code: value_text}
        language_code, localized_value = next(iter(raw_value.items()))
        if isinstance(localized_value, str):
            trimmed_value = localized_value.strip()
            trimmed_lang = language_code.strip()
            if trimmed_value and trimmed_lang:
                # Translators: A localized string value with its language code shown in parentheses.
                # "%(value)s" is the text content (quoted). %(language)s is the language code (e.g. "en").
                # Example: '"Temple" (en)'
                return _('"%(value)s" (%(language)s)') % {
                    "value": trimmed_value,
                    "language": trimmed_lang,
                }
            if trimmed_value:
                return f'"{trimmed_value}"'
        return ""

    # Check bool before int (isinstance(True, int) is True in Python)
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
        # Translators: A PATH operand value — a field in a related resource type.
        # "%(field)s" is the field name (quoted). "%(graph)s" is the resource type (quoted).
        # Example: 'the "Name" field in "Heritage Site"'
        return _('the "%(field)s" field in "%(graph)s"') % {
            "field": path_field_label,
            "graph": path_graph_label,
        }
    if path_graph_label:
        return f'"{path_graph_label}"'
    if path_field_label:
        # Translators: A PATH operand value — a field without an identified graph.
        # "%(field)s" is the field name (quoted label).
        # Example: 'the "Name" field'
        return _('the "%(field)s" field') % {"field": path_field_label}
    return ""


# ---------------------------------------------------------------------------
# Value list formatting
# ---------------------------------------------------------------------------


def _format_value_list(values: list) -> str:
    non_empty = [v.strip() for v in values if v.strip()]
    if not non_empty:
        return ""
    if len(non_empty) == 1:
        return non_empty[0]
    if len(non_empty) == 2:
        # Translators: Two values joined in a list for a search condition.
        # %(first)s and %(second)s are display values (may be quoted strings).
        # Chinese: use %(first)s和%(second)s (no comma or space around 和).
        # Arabic: use %(first)s و%(second)s (و is prefixed directly, no space before it).
        return _("%(first)s and %(second)s") % {
            "first": non_empty[0],
            "second": non_empty[1],
        }
    # Translators: Oxford-comma list of 3 or more values.
    # %(items)s is a comma-joined list of all values except the last.
    # %(last)s is the final value.
    # If your language does not use the Oxford comma, omit the comma before "and".
    # Example: '"Temple", "Acropolis", and "Parthenon"'
    return _("%(items)s, and %(last)s") % {
        "items": ", ".join(non_empty[:-1]),
        "last": non_empty[-1],
    }


# ---------------------------------------------------------------------------
# Relationship description
# ---------------------------------------------------------------------------


def _describe_relationship(
    relationship: dict, linked_graph_slug: str, ctx: NarrationContext
) -> str:
    path = relationship.get("path", {})
    graph_slug = (
        path.get("graph_slug") or ""
    ).strip()  # source graph — used for field label
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
            # Translators: ALL forward relationship — every linked record of this type must match.
            # "%(graph)s" is the linked resource type (quoted). "%(field)s" is the link field (quoted).
            # Example: 'where all linked "Activity" records (via "related site") match'
            return (
                _('where all linked "%(graph)s" records (via "%(field)s") match')
                % params
            )
        if quantifier == "NONE":
            # Translators: NONE forward relationship — no linked records of this type should match.
            # Example: 'with no linked "Activity" records (via "related site")'
            return _('with no linked "%(graph)s" records (via "%(field)s")') % params
        # ANY (default forward)
        # Translators: ANY forward relationship — at least one linked record must match.
        # "%(graph)s" is the linked resource type (quoted). "%(field)s" is the link field (quoted).
        # Example: 'with at least one linked "Activity" (via "related site")'
        return _('with at least one linked "%(graph)s" (via "%(field)s")') % params

    # Inverse direction: this record is referenced by others
    if quantifier == "ALL":
        # Translators: ALL inverse relationship — this record is the target of all records of this type.
        # "%(graph)s" is the referencing resource type (quoted). "%(field)s" is the reference field (quoted).
        # Example: 'referenced by all "Monument" records (via "mentioned site")'
        return _('referenced by all "%(graph)s" records (via "%(field)s")') % params
    if quantifier == "NONE":
        # Translators: NONE inverse relationship — this record is not referenced by any such record.
        # Example: 'not referenced by any "Monument" (via "mentioned site")'
        return _('not referenced by any "%(graph)s" (via "%(field)s")') % params
    # ANY inverse (default)
    # Translators: ANY inverse relationship — at least one record of this type references this record.
    # Example: 'referenced by at least one "Monument" (via "mentioned site")'
    return _('referenced by at least one "%(graph)s" (via "%(field)s")') % params
