"""
Data projected onto search results, beyond a resource's own serialization.

An entry takes the same two shapes a clause subject does, and uses the same
tokens, so one vocabulary covers filtering and projection alike:

    { "type": "NODE", "graph_slug": "person", "node_alias": "height" }
    { "type": "RESOURCE_FIELD", "field": "resource_instance_lifecycle_state" }

They are resolved together and read back split by kind, because the two name
spaces can collide -- a node aliased "principaluser" and the field of the same
name would otherwise fight over one key.
"""

from typing import Any, Dict, Iterable, List, Optional

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils.translation import gettext as _

from arches_search.utils.advanced_search.constants import (
    SUBJECT_TYPE_NODE,
    SUBJECT_TYPE_RESOURCE_FIELD,
)
from arches_search.utils.search.additional_data import node_values, resource_fields
from arches_search.utils.search.additional_data.node_values import (
    NodeColumnKey as NodeKey,
)

ENTRY_TYPES = (SUBJECT_TYPE_NODE, SUBJECT_TYPE_RESOURCE_FIELD)


def validate_additional_data(additional_data: Any) -> None:
    """
    Shape only. Whether a field exists is settled when it resolves, against the
    same registry a clause naming it would use.
    """
    if additional_data is None:
        return
    if not isinstance(additional_data, list):
        raise ValidationError(_("additional_data must be a list."))

    for index, entry in enumerate(additional_data):
        if not isinstance(entry, dict):
            raise ValidationError(
                _("additional_data[%(i)s] must be an object.") % {"i": index}
            )

        entry_type = entry.get("type")
        if entry_type not in ENTRY_TYPES:
            raise ValidationError(
                _("additional_data[%(i)s] type must be one of %(types)s.")
                % {"i": index, "types": ", ".join(ENTRY_TYPES)}
            )

        required_keys = (
            ("graph_slug", "node_alias")
            if entry_type == SUBJECT_TYPE_NODE
            else ("field",)
        )
        for key in required_keys:
            if not isinstance(entry.get(key), str) or not entry[key]:
                raise ValidationError(
                    _("additional_data[%(i)s] requires a non-empty %(key)s.")
                    % {"i": index, "key": key}
                )


def _entries_of_type(additional_data, entry_type):
    return [
        entry for entry in (additional_data or []) if entry.get("type") == entry_type
    ]


class AdditionalData:
    """
    The projections a search asked for, resolved once and then read per page.

    Resolution happens up front so the annotations can be applied before
    pagination -- ordering has to see the whole result set, and the values have
    to arrive with the page rather than costing a query per row.
    """

    def __init__(
        self,
        additional_data: Optional[List[Dict[str, Any]]],
        user,
        also_project_nodes: Iterable[NodeKey] = (),
    ):
        # also_project_nodes carries what an ordering needs. It is taken here
        # rather than added afterwards so there is no call order to get wrong: a
        # node added after annotate() would never be annotated, and the sort
        # would quietly fall back to no ordering at all.
        node_keys = node_values.keys(
            _entries_of_type(additional_data, SUBJECT_TYPE_NODE)
        )
        for node_key in also_project_nodes:
            if node_key not in node_keys:
                node_keys.append(node_key)

        self.nodes_by_key = node_values.resolve(node_keys, user)
        self.fields_by_name = resource_fields.resolve(
            resource_fields.field_names(
                _entries_of_type(additional_data, SUBJECT_TYPE_RESOURCE_FIELD)
            )
        )
        self.node_annotation_names: Dict[NodeKey, str] = {}
        self.field_annotation_names: Dict[str, Dict[str, Optional[str]]] = {}
        self._annotated = False

    def annotate(self, queryset: QuerySet) -> QuerySet:
        queryset, self.node_annotation_names = node_values.annotate(
            queryset, self.nodes_by_key
        )
        queryset, self.field_annotation_names = resource_fields.annotate(
            queryset, self.fields_by_name
        )
        self._annotated = True
        return queryset

    def format(self, resources) -> Dict[str, Dict[str, Any]]:
        if not self._annotated:
            # Every value is read from an annotation, so formatting first would
            # return a row of empty columns rather than fail.
            raise RuntimeError("annotate() must run before format().")

        node_data = node_values.format_values(
            resources, self.nodes_by_key, self.node_annotation_names
        )
        field_data = resource_fields.format_values(
            resources, self.fields_by_name, self.field_annotation_names
        )
        return {
            str(resource.pk): {
                "node_values": node_data.get(str(resource.pk), {}),
                "resource_fields": field_data.get(str(resource.pk), {}),
            }
            for resource in resources
        }
