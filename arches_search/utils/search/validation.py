"""
Shape checks for the search payload, run before anything compiles.

Each advanced search payload validates itself as it compiles, where the
registries are available; what is checked here is the shape of the keys around
them.
"""

import re
from functools import lru_cache
from typing import Any, Dict, FrozenSet, Set

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from arches.app.models.models import ResourceInstance, TileModel

from arches_search.utils.advanced_search.constants import (
    SUBJECT_TYPE_NODE,
    SUBJECT_TYPE_RESOURCE_FIELD,
)
from arches_search.utils.search.aggregation import AGGREGATE_FUNCTIONS
from arches_search.utils.term_search.relationship_expansion import MAX_ALLOWED_HOPS

# Every key an aggregation may carry. Anything else is refused, not ignored.
AGGREGATION_KEYS = frozenset(
    {"name", "group_by", "metrics", "aggregate", "aggregate_by_tile"}
)
NODE_SPEC_KEYS = frozenset(
    {
        "type",
        "alias",
        "graph_slug",
        "node_alias",
        "fn",
        "aggregate_by_tile",
        "aggregations",
    }
)
RESOURCE_FIELD_SPEC_KEYS = frozenset({"type", "alias", "field", "fn"})
NESTED_AGGREGATION_KEYS = frozenset({"group_by"})
SIMPLE_AGGREGATE_KEYS = frozenset({"alias", "fn", "field", "distinct"})

# Min and Max reject distinct=True.
DISTINCT_AGGREGATE_FUNCTIONS = frozenset({"Count", "Sum", "Avg"})

# An alias becomes an annotation name, so it has to be one Django accepts.
ALIAS_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _positive_integer(value) -> bool:
    # bool is an int subclass, and True would otherwise pass as page 1.
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def validate_paging(page, page_size) -> None:
    """
    Checked here so bad paging is a 400. Left to Paginator, a non-integer page
    raises PageNotAnInteger and page_size 0 raises ZeroDivisionError -- neither
    is a ValidationError, so both would surface as a 500.

    The ceiling is core's API_MAX_PAGE_SIZE, the limit its own APIs page by.
    """
    if not _positive_integer(page):
        raise ValidationError(_("page must be a positive integer."))

    max_page_size = settings.API_MAX_PAGE_SIZE
    if not _positive_integer(page_size) or page_size > max_page_size:
        raise ValidationError(
            _("page_size must be an integer between 1 and %(max)s.")
            % {"max": max_page_size}
        )


def _is_valid_term(term) -> bool:
    # A string matches any datatype; an object restricts its text to one
    # TermSearch datatype, which is how a controlled term stays a reference.
    if isinstance(term, str):
        return bool(term)
    return (
        isinstance(term, dict)
        and isinstance(term.get("text"), str)
        and bool(term["text"])
        and isinstance(term.get("datatype"), str)
        and bool(term["datatype"])
    )


def validate_term_search(term_search):
    """
    One object, not a list of typed entries.

    The geometry and date filters that used to sit beside this are advanced
    search clauses now, so there is nothing left to discriminate between.
    """
    if term_search is None:
        return

    if not isinstance(term_search, dict):
        raise ValidationError(_("term_search must be an object."))

    terms = term_search.get("terms")
    if not isinstance(terms, list) or not all(_is_valid_term(term) for term in terms):
        raise ValidationError(
            _(
                "term_search terms must be a list of non-empty strings, or of "
                "objects with a non-empty text and datatype."
            )
        )

    max_hops = term_search.get("max_hops", 0)
    if (
        not isinstance(max_hops, int)
        or isinstance(max_hops, bool)
        or not (0 <= max_hops <= MAX_ALLOWED_HOPS)
    ):
        raise ValidationError(
            _("term_search max_hops must be an integer between 0 and %(max)s.")
            % {"max": MAX_ALLOWED_HOPS}
        )


def validate_advanced_search_queries(advanced_search_queries):
    """
    Check the shape of the list itself; each entry is validated as it compiles.

    Two entries for one graph would mean one of them is silently ignored, so
    that is rejected rather than resolved by ordering.
    """
    if advanced_search_queries is None:
        return

    if not isinstance(advanced_search_queries, list):
        raise ValidationError(
            _("advanced_search_queries must be a list of advanced search payloads.")
        )

    seen_graph_slugs = set()
    for index, graph_payload in enumerate(advanced_search_queries):
        if not isinstance(graph_payload, dict):
            raise ValidationError(
                _("advanced_search_queries[%(index)s] must be an object."),
                params={"index": index},
            )

        graph_slug = graph_payload.get("graph_slug")
        if not isinstance(graph_slug, str) or not graph_slug:
            raise ValidationError(
                _(
                    "advanced_search_queries[%(index)s] requires a non-empty "
                    "graph_slug naming the resource model it filters."
                ),
                params={"index": index},
            )

        if graph_slug in seen_graph_slugs:
            raise ValidationError(
                _(
                    "advanced_search_queries has more than one entry for graph "
                    "%(graph_slug)s; each graph may be addressed once."
                ),
                params={"graph_slug": graph_slug},
            )
        seen_graph_slugs.add(graph_slug)


def validate_graph_slugs(graph_slugs):
    """
    The selector itself: which resource models are searched.

    A bare string would otherwise be iterated a character at a time, selecting
    no resource model and returning nothing -- a search that looks like it ran
    and found no matches.
    """
    if graph_slugs is None:
        return

    if not isinstance(graph_slugs, list) or not all(
        isinstance(graph_slug, str) and graph_slug for graph_slug in graph_slugs
    ):
        raise ValidationError(_("graph_slugs must be a list of non-empty strings."))


def validate_aggregations(aggregations) -> None:
    """
    Only the keys listed above are accepted, so nothing in an aggregation
    reaches the ORM as a lookup, a table name or a field path.

    Shape only. Whether a node or field exists is checked when the aggregation
    runs, against the same registries a clause uses.
    """
    if aggregations is None:
        return
    if not isinstance(aggregations, list):
        raise ValidationError(_("aggregations must be a list."))

    result_names: Set[str] = set()
    for index, aggregation in enumerate(aggregations):
        location = f"aggregations[{index}]"
        _require_object(aggregation, location)
        _refuse_unknown_keys(aggregation, AGGREGATION_KEYS, location)
        _claim_result_name(aggregation.get("name"), f"{location}.name", result_names)
        _require_optional_boolean(aggregation, "aggregate_by_tile", location)

        group_by = aggregation.get("group_by")
        # Without a column to group by, the rows themselves would come back.
        if not isinstance(group_by, list) or not group_by:
            raise ValidationError(
                _("%(location)s.group_by must be a non-empty list."),
                params={"location": location},
            )
        metrics = aggregation.get("metrics", [])
        if not isinstance(metrics, list):
            raise ValidationError(
                _("%(location)s.metrics must be a list."),
                params={"location": location},
            )

        column_aliases: Set[str] = set()
        for key, specs in (("group_by", group_by), ("metrics", metrics)):
            for spec_index, spec in enumerate(specs):
                spec_location = f"{location}.{key}[{spec_index}]"
                _validate_spec(spec, spec_location, requires_fn=key == "metrics")
                if spec["alias"] in column_aliases:
                    raise ValidationError(
                        _("%(location)s.alias %(alias)s is already used."),
                        params={"location": spec_location, "alias": spec["alias"]},
                    )
                column_aliases.add(spec["alias"])

        group_by_aliases = {spec["alias"] for spec in group_by}
        simple_aggregates = aggregation.get("aggregate", [])
        if not isinstance(simple_aggregates, list):
            raise ValidationError(
                _("%(location)s.aggregate must be a list."),
                params={"location": location},
            )
        for aggregate_index, aggregate in enumerate(simple_aggregates):
            aggregate_location = f"{location}.aggregate[{aggregate_index}]"
            _validate_simple_aggregate(
                aggregate, aggregate_location, group_by_aliases, result_names
            )


def _validate_spec(spec: Any, location: str, requires_fn: bool) -> None:
    _require_object(spec, location)

    spec_type = spec.get("type")
    if spec_type == SUBJECT_TYPE_NODE:
        _refuse_unknown_keys(spec, NODE_SPEC_KEYS, location)
        _require_string(spec, "graph_slug", location)
        _require_string(spec, "node_alias", location)
        _require_optional_boolean(spec, "aggregate_by_tile", location)
        _validate_nested_aggregations(spec.get("aggregations", []), location)
    elif spec_type == SUBJECT_TYPE_RESOURCE_FIELD:
        _refuse_unknown_keys(spec, RESOURCE_FIELD_SPEC_KEYS, location)
        _require_string(spec, "field", location)
    else:
        raise ValidationError(
            _("%(location)s.type must be one of %(types)s."),
            params={
                "location": location,
                "types": ", ".join((SUBJECT_TYPE_NODE, SUBJECT_TYPE_RESOURCE_FIELD)),
            },
        )

    _require_alias(spec, location)
    if requires_fn or "fn" in spec:
        _require_function(spec, location)


def _validate_nested_aggregations(nested_aggregations: Any, location: str) -> None:
    if not isinstance(nested_aggregations, list):
        raise ValidationError(
            _("%(location)s.aggregations must be a list."),
            params={"location": location},
        )

    for nested_index, nested_aggregation in enumerate(nested_aggregations):
        nested_location = f"{location}.aggregations[{nested_index}]"
        _require_object(nested_aggregation, nested_location)
        _refuse_unknown_keys(
            nested_aggregation, NESTED_AGGREGATION_KEYS, nested_location
        )
        nested_group_by = nested_aggregation.get("group_by", [])
        if not isinstance(nested_group_by, list):
            raise ValidationError(
                _("%(location)s.group_by must be a list."),
                params={"location": nested_location},
            )
        for spec_index, nested_spec in enumerate(nested_group_by):
            spec_location = f"{nested_location}.group_by[{spec_index}]"
            _require_object(nested_spec, spec_location)
            # A nested group follows a node's value, so only a node can nest.
            if nested_spec.get("type") != SUBJECT_TYPE_NODE:
                raise ValidationError(
                    _("%(location)s.type must be %(type)s."),
                    params={"location": spec_location, "type": SUBJECT_TYPE_NODE},
                )
            _validate_spec(nested_spec, spec_location, requires_fn=False)


def _validate_simple_aggregate(
    aggregate: Any,
    location: str,
    group_by_aliases: Set[str],
    result_names: Set[str],
) -> None:
    _require_object(aggregate, location)
    _refuse_unknown_keys(aggregate, SIMPLE_AGGREGATE_KEYS, location)
    _claim_result_name(aggregate.get("alias"), f"{location}.alias", result_names)
    _require_function(aggregate, location)
    _require_optional_boolean(aggregate, "distinct", location)

    # Only a grouped column, never a path: a path is how a field outside the
    # search results would be read.
    if aggregate.get("field") not in group_by_aliases:
        raise ValidationError(
            _("%(location)s.field must be one of this aggregation's group_by aliases."),
            params={"location": location},
        )

    if (
        aggregate.get("distinct")
        and aggregate["fn"] not in DISTINCT_AGGREGATE_FUNCTIONS
    ):
        raise ValidationError(
            _("%(location)s.distinct is not supported with %(fn)s."),
            params={"location": location, "fn": aggregate["fn"]},
        )


def _require_object(value: Any, location: str) -> None:
    if not isinstance(value, dict):
        raise ValidationError(
            _("%(location)s must be an object."), params={"location": location}
        )


def _refuse_unknown_keys(
    value: Dict[str, Any], allowed_keys: FrozenSet[str], location: str
) -> None:
    unknown_keys = sorted(set(value) - allowed_keys)
    if unknown_keys:
        raise ValidationError(
            _("%(location)s does not accept %(keys)s."),
            params={"location": location, "keys": ", ".join(unknown_keys)},
        )


def _require_string(value: Dict[str, Any], key: str, location: str) -> None:
    if not isinstance(value.get(key), str) or not value[key]:
        raise ValidationError(
            _("%(location)s requires a non-empty %(key)s."),
            params={"location": location, "key": key},
        )


def _require_optional_boolean(value: Dict[str, Any], key: str, location: str) -> None:
    if key in value and not isinstance(value[key], bool):
        raise ValidationError(
            _("%(location)s.%(key)s must be true or false."),
            params={"location": location, "key": key},
        )


def _require_function(value: Dict[str, Any], location: str) -> None:
    if value.get("fn") not in AGGREGATE_FUNCTIONS:
        raise ValidationError(
            _("%(location)s.fn must be one of %(functions)s."),
            params={"location": location, "functions": ", ".join(AGGREGATE_FUNCTIONS)},
        )


def _require_alias(value: Dict[str, Any], location: str) -> None:
    alias = value.get("alias")
    if (
        not isinstance(alias, str)
        or not ALIAS_PATTERN.match(alias)
        or "__" in alias
        or alias in _row_field_names()
    ):
        raise ValidationError(
            _(
                "%(location)s.alias must be a letter followed by letters, digits "
                "or single underscores, and must not name a column of the rows "
                "being aggregated."
            ),
            params={"location": location},
        )


def _claim_result_name(name: Any, location: str, result_names: Set[str]) -> None:
    """Aggregation names and simple aggregate aliases share one results object."""
    if not isinstance(name, str) or not name:
        raise ValidationError(
            _("%(location)s must be a non-empty string."), params={"location": location}
        )
    if name in result_names:
        raise ValidationError(
            _("%(location)s %(name)s is already used."),
            params={"location": location, "name": name},
        )
    result_names.add(name)


@lru_cache(maxsize=None)
def _row_field_names() -> FrozenSet[str]:
    """
    Columns of the rows an aggregation annotates, which an alias would collide
    with. Read from model metadata, so no query is made.
    """
    return frozenset(
        name
        for model_class in (ResourceInstance, TileModel)
        for field in model_class._meta.get_fields()
        for name in (field.name, getattr(field, "attname", field.name))
    )


def validate_search_payload(search_payload) -> None:
    """
    Every check that applies to the filtering half of a request.

    Grouped so the endpoints that compile a payload without running a whole
    search -- the export, the map tiles -- cannot drift out of step with the
    search endpoint on what they accept.
    """
    validate_graph_slugs(search_payload.graph_slugs)
    validate_term_search(search_payload.term_search)
    validate_advanced_search_queries(search_payload.advanced_search_queries)
