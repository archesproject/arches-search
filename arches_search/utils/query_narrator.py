from django.conf import settings
from django.utils import translation
from django.utils.translation import (
    get_language,
    get_language_bidi,
    gettext as _,
    pgettext,
)

from arches.app.models import models as arches_models

from arches_search.models.models import AdvancedSearchFacet
from arches_search.utils.node_alias_metadata import (
    build_node_alias_metadata_for_payload_query,
)
from arches_search.utils.resource_names_for_payload import (
    build_resource_names_for_payload,
)


class QueryNarrator:
    def __init__(self, payload: dict, language_code: str | None = None):
        self._payload = payload
        self._language_code = language_code or get_language() or settings.LANGUAGE_CODE

    def narrate(self) -> str:
        if not self._payload.get("graph_slug"):
            return ""
        with translation.override(self._language_code):
            self._build_context()
            lines = self._describe_group(self._payload, depth=0)
            return self._render(lines)

    def _build_context(self) -> None:
        node_metadata = build_node_alias_metadata_for_payload_query(self._payload)
        self._graph_names = {
            str(graph.slug): str(graph.name)
            for graph in arches_models.GraphModel.objects.filter(
                slug__in=self._collect_graph_slugs(self._payload)
            )
        }
        self._node_labels = {
            alias_key: alias_metadata["card_x_node_x_widget_label"]
            for alias_key, alias_metadata in node_metadata.items()
        }
        self._node_datatypes = {
            alias_key: alias_metadata["datatype"]
            for alias_key, alias_metadata in node_metadata.items()
        }
        self._operator_labels = {
            facet.operator: label
            for facet in AdvancedSearchFacet.objects.all()
            if facet.operator and (label := str(facet.label))
        }
        self._resource_names = build_resource_names_for_payload(self._payload)
        self._is_rtl = get_language_bidi()

    @staticmethod
    def _collect_graph_slugs(payload: dict) -> set:
        slugs = set()

        if slug := payload.get("graph_slug"):
            slugs.add(slug)

        for clause in payload.get("clauses", []):
            if slug := clause.get("subject", {}).get("graph_slug"):
                slugs.add(slug)
            for operand in clause.get("operands", []):
                if operand.get("type") == "PATH":
                    path = operand.get("value") or []
                    # path is a list of [graph_slug, node_alias] segments;
                    # path[-1] is the terminal segment, index 0 is its graph_slug.
                    if path and isinstance(path[-1], list) and path[-1]:
                        slugs.add(path[-1][0])

        if (
            slug := (payload.get("relationship") or {})
            .get("path", {})
            .get("graph_slug")
        ):
            slugs.add(slug)

        for subgroup in payload.get("groups", []):
            slugs.update(QueryNarrator._collect_graph_slugs(subgroup))

        return slugs

    def _render(self, lines: list) -> str:
        graph_slug = self._payload["graph_slug"]
        graph_label = self._graph_names.get(graph_slug, graph_slug)
        if not lines:
            return _('All "%(graph)s" records.') % {"graph": graph_label}
        intro = _('All "%(graph)s" records where:') % {"graph": graph_label}
        return intro + "\n" + "\n".join(lines)

    @staticmethod
    def _indent_prefix(depth: int, is_rtl: bool) -> str:
        # U+200F anchors bidi base direction so the bullet renders at the right edge in RTL.
        return ("‏" if is_rtl else "") + "    " * depth + "• "

    def _describe_group(self, group: dict, depth: int) -> list:
        logic = group.get("logic", "AND")
        prefix = self._indent_prefix(depth, self._is_rtl)
        result = []

        clause_phrases = [
            phrase
            for clause in group.get("clauses", [])
            if (phrase := self._describe_clause(clause))
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
            # groups[0] is the linked graph's condition block; groups[1:] are siblings.
            linked_subgroup = subgroups[0] if subgroups else None
            sibling_subgroups = subgroups[1:]
            result.extend(
                self._describe_relationship_block(
                    relationship=relationship,
                    linked_subgroup=linked_subgroup,
                    sibling_subgroups=sibling_subgroups,
                    depth=depth,
                    prefix=prefix,
                    has_prior_clauses=bool(clause_phrases),
                    logic=logic,
                )
            )
        else:
            for subgroup in subgroups:
                result.extend(self._describe_group(subgroup, depth))

        return result

    def _describe_relationship_block(
        self,
        relationship: dict,
        linked_subgroup: dict | None,
        sibling_subgroups: list,
        depth: int,
        prefix: str,
        has_prior_clauses: bool,
        logic: str,
    ) -> list:
        linked_graph_slug = (
            linked_subgroup.get("graph_slug", "") if linked_subgroup else ""
        )
        relationship_phrase = self._describe_relationship(
            relationship, linked_graph_slug
        )

        lines = []
        if relationship_phrase:
            inner_lines = (
                self._describe_group(linked_subgroup, depth + 1)
                if linked_subgroup
                else []
            )
            full_phrase = relationship_phrase + (":" if inner_lines else "")
            if logic == "OR" and has_prior_clauses:
                lines.append(
                    prefix + _("OR: %(condition)s") % {"condition": full_phrase}
                )
            else:
                lines.append(prefix + full_phrase)
            lines.extend(inner_lines)

        for sibling in sibling_subgroups:
            lines.extend(self._describe_group(sibling, depth))

        return lines

    def _describe_clause(self, clause: dict) -> str:
        field_label = self._resolve_clause_field_label(clause)
        operator = clause.get("operator", "")
        if not field_label or not operator:
            return ""

        operator_label = self._operator_labels.get(operator, operator)
        subject = clause.get("subject", {})
        datatype = ""
        if subject.get("type") == "NODE":
            datatype = self._node_datatypes.get(
                (subject.get("graph_slug"), subject.get("node_alias")), ""
            )

        value_phrase = self._format_value_list(
            [
                operand_description
                for operand in clause.get("operands", [])
                if (operand_description := self._describe_operand(operand, datatype))
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

    def _resolve_clause_field_label(self, clause: dict) -> str:
        subject = clause.get("subject", {})
        subject_type = subject.get("type")
        graph_slug = subject.get("graph_slug")
        if not graph_slug:
            return ""

        if subject_type == "NODE":
            node_alias = subject.get("node_alias")
            if node_alias:
                return self._node_labels.get((graph_slug, node_alias), "") or node_alias

        if subject_type == "SEARCH_MODELS" and subject.get("search_models"):
            graph_label = self._graph_names.get(graph_slug, graph_slug)
            return (
                _('any field in "%(graph)s"') % {"graph": graph_label}
                if graph_label
                else _("any field")
            )

        return ""

    def _describe_operand(self, operand: dict, subject_datatype: str) -> str:
        if operand.get("type") == "PATH":
            return self._describe_path_value(operand.get("value"))

        display_value = operand.get("display_value")
        if display_value is None:
            display_value = operand.get("value")
        if display_value is None:
            return ""

        if isinstance(display_value, list):
            return self._format_value_list(
                [
                    self._quote(self._resource_names.get(item, item))
                    for item in display_value
                    if isinstance(item, str)
                ]
            )

        if (
            subject_datatype == "string"
            and isinstance(display_value, dict)
            and len(display_value) == 1
        ):
            ((language_code, text),) = display_value.items()
            if not isinstance(text, str) or not text.strip():
                return ""
            text = text.strip()
            if language_code:
                return _('"%(value)s" (%(language)s)') % {
                    "value": text,
                    "language": language_code,
                }
            return self._quote(text)

        # bool must be checked before int: isinstance(True, int) is True
        if isinstance(display_value, bool):
            return _("true") if display_value else _("false")

        if isinstance(display_value, (int, float)):
            return str(display_value)

        text = str(display_value).strip()
        return self._quote(text) if text else ""

    def _describe_path_value(self, path_value) -> str:
        if not isinstance(path_value, list) or not path_value:
            return ""
        last_entry = path_value[-1]
        if not isinstance(last_entry, list) or len(last_entry) < 2:
            return ""

        path_graph_slug, path_node_alias = last_entry[0], last_entry[1]
        graph_label = self._graph_names.get(path_graph_slug, path_graph_slug)
        field_label = (
            self._node_labels.get((path_graph_slug, path_node_alias), "")
            or path_node_alias
        )

        if graph_label and field_label:
            return _('the "%(field)s" field in "%(graph)s"') % {
                "field": field_label,
                "graph": graph_label,
            }
        if graph_label:
            return self._quote(graph_label)
        if field_label:
            return _('the "%(field)s" field') % {"field": field_label}
        return ""

    def _describe_relationship(self, relationship: dict, linked_graph_slug: str) -> str:
        relationship_path = relationship.get("path", {})
        source_graph_slug = relationship_path.get("graph_slug")
        node_alias = relationship_path.get("node_alias")

        template_params = {
            "graph": self._graph_names.get(linked_graph_slug, linked_graph_slug),
            "field": self._node_labels.get((source_graph_slug, node_alias), "")
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
                _('not referenced by any "%(graph)s" (via "%(field)s")')
                % template_params
            )
        return (
            _('referenced by at least one "%(graph)s" (via "%(field)s")')
            % template_params
        )

    @staticmethod
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
        list_separator = pgettext("list separator for 3 or more items", ", ")
        return _("%(items)s, and %(last)s") % {
            "items": list_separator.join(non_empty[:-1]),
            "last": non_empty[-1],
        }

    @staticmethod
    def _quote(text: str) -> str:
        return _('"%(value)s"') % {"value": text}
