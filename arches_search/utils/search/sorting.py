from typing import Any, Dict, List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db.models import (
    F,
    FilteredRelation,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    TextField,
)
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Lower
from django.utils.translation import get_language, gettext as _

from arches.app.models.models import Node

from arches_search.indexing.indexing_factory import IndexingFactory
from arches_search.utils.advanced_search.constants import (
    SUBJECT_TYPE_NODE,
    SUBJECT_TYPE_RESOURCE_FIELD,
)
from arches_search.utils.advanced_search.registries.search_model_registry import (
    SearchModelRegistry,
)
from arches_search.utils.resource_field_search.labels import label_expression
from arches_search.utils.resource_field_search.field_registry import (
    ResourceInstanceFieldRegistry,
    get_resource_instance_fields,
)

SORT_TYPE_PRIMARY_NAME = "primary_name"
SORT_TYPE_CREATED_TIME = "created_time"
# The same tokens a clause subject and an additional_data entry use.
SORT_TYPE_RESOURCE_FIELD = SUBJECT_TYPE_RESOURCE_FIELD
SORT_TYPE_NODE = SUBJECT_TYPE_NODE
DIRECTION_ASC = "asc"
DIRECTION_DESC = "desc"

ALLOWED_DIRECTIONS = {DIRECTION_ASC, DIRECTION_DESC}
ALLOWED_SORT_TYPES = {
    SORT_TYPE_PRIMARY_NAME,
    SORT_TYPE_CREATED_TIME,
    SORT_TYPE_RESOURCE_FIELD,
    SORT_TYPE_NODE,
}

# Applied when the payload names no sort. Empty means no user-visible ordering;
# the id tie-break still runs.
DEFAULT_SORT: List[Dict[str, Any]] = []

Ordering = Any


def _ordering(field: F, spec: Dict[str, Any], nulls_last: Optional[bool] = None):
    # nulls_last must be True or None; Django rejects False.
    if spec.get("direction", DIRECTION_ASC) == DIRECTION_ASC:
        return field.asc(nulls_last=nulls_last)
    return field.desc(nulls_last=nulls_last)


def _node_indexes_several_rows(node: Node) -> bool:
    """Whether one resource can hold several indexed rows for this node."""
    if (node.config or {}).get("multiValue"):
        return True

    nodegroup = node.nodegroup
    while nodegroup is not None:
        if nodegroup.cardinality == "n":
            return True
        nodegroup = nodegroup.parentnodegroup

    return False


def _sort_key(search_model: Any, value_path: str) -> Any:
    """Fold text, so "Zebra" does not lead "apple". Anything else sorts as stored."""
    if isinstance(search_model._meta.get_field("value"), TextField):
        return Lower(value_path)
    return F(value_path)


def _indexed_row_filters(search_model: Any, node: Node) -> Dict[str, Any]:
    """Which of a node's indexed rows an ordering reads."""
    filters = {"graph_slug": node.graph.slug, "node_alias": node.alias}
    model_fields = {field.name for field in search_model._meta.get_fields()}

    if "language" in model_fields:
        # A value carrying no language of its own indexes an empty one.
        filters["language__in"] = (get_language(), "")

    filters.update(
        IndexingFactory().get_indexing_class(node.datatype).sort_row_filters()
    )
    return filters


class SortResolver:
    """
    Applies sort specs to a ResourceInstance queryset.

    A spec is {"type": ..., "direction": "asc"|"desc"} plus whatever the type
    needs: "field" for RESOURCE_FIELD, "graph_slug"/"node_alias" for NODE.

    A NODE sort joins the search table already holding that node's indexed
    value -- the same table filtering reads -- and orders by it, so the
    database does no per-row work. Callers pass the nodes it may sort by as
    sort_nodes; a node the requester cannot read is simply absent from that
    map, and is skipped rather than reported.

    A tie-break on resourceinstanceid is always appended, so paging is stable.
    """

    def __init__(self, sort_specs: Optional[List[Dict[str, Any]]] = None) -> None:
        if sort_specs is None:
            sort_specs = DEFAULT_SORT
        self._resource_field_registry: Optional[ResourceInstanceFieldRegistry] = None
        self._search_model_registry: Optional[SearchModelRegistry] = None
        self._validate(sort_specs)
        self.sort_specs = sort_specs

    @property
    def search_model_registry(self) -> SearchModelRegistry:
        """Built on first use, like the resource field registry: it costs a query."""
        if self._search_model_registry is None:
            self._search_model_registry = SearchModelRegistry()
        return self._search_model_registry

    @property
    def resource_field_registry(self) -> ResourceInstanceFieldRegistry:
        """Built on first use: it costs a query, and most searches never sort by one."""
        if self._resource_field_registry is None:
            self._resource_field_registry = get_resource_instance_fields()
        return self._resource_field_registry

    def apply(
        self,
        queryset: QuerySet,
        sort_nodes: Optional[Dict[Any, Node]] = None,
    ) -> QuerySet:
        sort_nodes = sort_nodes or {}
        order_expressions: List[Ordering] = []

        for index, spec in enumerate(self.sort_specs):
            sort_type = spec["type"]
            if sort_type == SORT_TYPE_PRIMARY_NAME:
                queryset, ordering = self._primary_name(queryset, spec, index)
            elif sort_type == SORT_TYPE_CREATED_TIME:
                queryset, ordering = self._created_time(queryset, spec)
            elif sort_type == SORT_TYPE_RESOURCE_FIELD:
                queryset, ordering = self._resource_field(queryset, spec, index)
            else:
                queryset, ordering = self._node_value(queryset, spec, index, sort_nodes)

            if ordering is not None:
                order_expressions.append(ordering)

        order_expressions.append(F("resourceinstanceid").asc())
        return queryset.order_by(*order_expressions)

    def _primary_name(
        self, queryset: QuerySet, spec: Dict[str, Any], index: int
    ) -> Tuple[QuerySet, Ordering]:
        annotation = f"_sort_primary_name_{index}"
        queryset = queryset.annotate(
            **{
                annotation: Lower(
                    KeyTextTransform(
                        "name", KeyTextTransform(get_language() or "en", "descriptors")
                    )
                )
            }
        )
        return queryset, _ordering(F(annotation), spec)

    def _created_time(
        self, queryset: QuerySet, spec: Dict[str, Any]
    ) -> Tuple[QuerySet, Ordering]:
        return queryset, _ordering(F("createdtime"), spec)

    def _resource_field(
        self, queryset: QuerySet, spec: Dict[str, Any], index: int
    ) -> Tuple[QuerySet, Ordering]:
        descriptor = self.resource_field_registry.get(spec["field"])

        # Order a foreign key by the related record's label, not its raw id.
        # Lower() lives here, not in label_expression: projection wants the
        # label as stored.
        label = label_expression(descriptor)
        if label is None:
            sort_field = F(descriptor.orm_path)
        else:
            annotation = f"_sort_resource_field_{index}"
            queryset = queryset.annotate(**{annotation: Lower(label)})
            sort_field = F(annotation)

        # A nullable column would otherwise lead on DESC in Postgres.
        return queryset, _ordering(sort_field, spec, nulls_last=True)

    def _node_value(
        self,
        queryset: QuerySet,
        spec: Dict[str, Any],
        index: int,
        sort_nodes: Dict[Any, Node],
    ) -> Tuple[QuerySet, Ordering]:
        """
        Order by the node's indexed value; joined rather than recomputed per resource.
        """
        node = sort_nodes.get((spec["graph_slug"], spec["node_alias"]))
        if node is None:
            return queryset, None

        search_model = self.search_model_registry.get_sort_model_for_datatype(
            node.datatype
        )
        if search_model is None:
            return queryset, None

        row_filters = _indexed_row_filters(search_model, node)
        annotation = f"_sort_node_{index}"

        if _node_indexes_several_rows(node):
            first_tile_value = (
                search_model.objects.filter(
                    resourceinstanceid=OuterRef("resourceinstanceid"), **row_filters
                )
                .annotate(sort_key=_sort_key(search_model, "value"))
                # tileid breaks the tie: sortorder is not unique in practice,
                # and without it the row picked varies between queries.
                .order_by("tileid__parenttile", "tileid__sortorder", "tileid")
                .values("sort_key")[:1]
            )
            queryset = queryset.annotate(**{annotation: Subquery(first_tile_value)})
            return queryset, _ordering(F(annotation), spec, nulls_last=True)

        relation = search_model._meta.model_name
        queryset = queryset.annotate(
            **{
                annotation: FilteredRelation(
                    relation,
                    condition=Q(
                        **{
                            f"{relation}__{field}": value
                            for field, value in row_filters.items()
                        }
                    ),
                )
            }
        )
        return queryset, _ordering(
            _sort_key(search_model, f"{annotation}__value"), spec, nulls_last=True
        )

    def _validate(self, sort_specs: Any) -> None:
        if not isinstance(sort_specs, list):
            raise ValidationError(_("sort must be a list of sort specs."))

        for index, spec in enumerate(sort_specs):
            if not isinstance(spec, dict):
                raise ValidationError(
                    _("sort[%(i)s] must be an object.") % {"i": index}
                )

            sort_type = spec.get("type")
            if sort_type not in ALLOWED_SORT_TYPES:
                raise ValidationError(
                    _("sort[%(i)s] has unsupported type %(type)s.")
                    % {"i": index, "type": sort_type}
                )

            if sort_type == SORT_TYPE_RESOURCE_FIELD:
                field_name = spec.get("field")
                if (
                    not isinstance(field_name, str)
                    or self.resource_field_registry.get(field_name) is None
                ):
                    raise ValidationError(
                        _("sort[%(i)s] has unsupported field %(field)s.")
                        % {"i": index, "field": field_name}
                    )

            if sort_type == SORT_TYPE_NODE:
                for key in ("graph_slug", "node_alias"):
                    if not isinstance(spec.get(key), str) or not spec[key]:
                        raise ValidationError(
                            _("sort[%(i)s] requires a non-empty %(key)s.")
                            % {"i": index, "key": key}
                        )

            if spec.get("direction", DIRECTION_ASC) not in ALLOWED_DIRECTIONS:
                raise ValidationError(
                    _("sort[%(i)s] direction must be one of asc, desc.") % {"i": index}
                )
