"""
The ResourceInstance fields that search can filter, sort, and group by.

Fields come from the model and are joined to their AdvancedSearchFacet rows, so
a field is queryable exactly when facets exist for its Django field class.

Related models are reachable one hop, and only via their label field
(``username`` for the user model, ``name`` otherwise), which is what keeps
columns such as ``principaluser__password`` unreachable.
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.module_loading import import_string

from arches.app.models.models import ResourceInstance

# Names tried, in order, when hopping to a related model's label. Searched
# rather than mapped per model, so a relation Arches adds later resolves without
# a change here.
LABEL_FIELD_CANDIDATES = ("name", "username", "label", "title")

# Related models bounded enough to enumerate as pick-list choices. Overridable,
# since which models qualify is a project's judgement, not a fixed fact.
DEFAULT_CHOICE_ENUMERABLE_MODELS = frozenset({"ResourceInstanceLifecycleState"})

CURRENT_USER_FORMAT = "current_user"


@dataclass(frozen=True)
class ResourceInstanceField:
    """One queryable field, as exposed to clients."""

    name: str
    orm_path: str
    facets: Dict[str, Any]
    label: str = ""
    kind: str = ""
    is_groupable: bool = False
    is_user_relation: bool = False
    is_nullable: bool = False
    related_model_name: str = ""
    # Foreign keys sort by the related record's label, not its primary key.
    label_orm_path: Optional[str] = None
    label_is_i18n_json: bool = False
    label_is_text: bool = False

    @property
    def operators(self) -> Tuple[str, ...]:
        return tuple(self.facets)

    def supports(self, operator: str) -> bool:
        return operator in self.facets

    def facet_for(self, operator: str) -> Optional[Any]:
        return self.facets.get(operator)

    @property
    def has_enumerable_choices(self) -> bool:
        return self.related_model_name in _choice_enumerable_models()


class ResourceInstanceFieldRegistry:
    """
    The single source of truth for which fields are queryable.

    Filtering, sorting, grouping and the metadata endpoint all resolve here, so
    the four cannot drift apart.
    """

    def __init__(self, model=ResourceInstance) -> None:
        self.model = model
        self._fields: Dict[str, ResourceInstanceField] = self._discover()

    def get(self, field_name: str) -> Optional[ResourceInstanceField]:
        return self._fields.get(field_name)

    def names(self) -> Tuple[str, ...]:
        return tuple(sorted(self._fields))

    def all(self) -> Tuple[ResourceInstanceField, ...]:
        return tuple(self._fields[name] for name in self.names())

    def groupable(self) -> Tuple[ResourceInstanceField, ...]:
        return tuple(field for field in self.all() if field.is_groupable)

    def _discover(self) -> Dict[str, ResourceInstanceField]:
        fields: Dict[str, ResourceInstanceField] = {}

        for model_field in self.model._meta.get_fields():
            if not _is_scalar_column(model_field):
                continue

            is_relation = bool(model_field.many_to_one or model_field.one_to_one)
            related_model = model_field.related_model if is_relation else None
            is_user_relation = is_relation and related_model is get_user_model()

            facets = _facets_for(model_field, allow_current_user=is_user_relation)
            if not facets:
                continue

            label_name, label_field = _label_field_for(related_model)
            label_orm_path = f"{model_field.name}__{label_name}" if label_name else None

            fields[model_field.name] = _build_field(
                name=model_field.name,
                orm_path=model_field.attname,
                model_field=model_field,
                facets=facets,
                kind=model_field.get_internal_type(),
                is_groupable=_is_groupable(model_field),
                is_user_relation=is_user_relation,
                related_model=related_model,
                label_orm_path=label_orm_path,
                label_field=label_field,
            )

            if label_orm_path and label_field is not None:
                label_facets = _facets_for(label_field)
                if label_facets:
                    fields[label_orm_path] = _build_field(
                        name=label_orm_path,
                        orm_path=label_orm_path,
                        model_field=label_field,
                        facets=label_facets,
                        kind=label_field.get_internal_type(),
                        is_user_relation=is_user_relation,
                        related_model=related_model,
                        fallback_label=label_name,
                    )

        return fields


def _build_field(
    *,
    name: str,
    orm_path: str,
    model_field,
    facets: Dict[str, Any],
    kind: str,
    is_user_relation: bool,
    related_model,
    is_groupable: bool = False,
    label_orm_path: Optional[str] = None,
    label_field=None,
    fallback_label: str = "",
) -> ResourceInstanceField:
    return ResourceInstanceField(
        name=name,
        orm_path=orm_path,
        facets=facets,
        label=str(getattr(model_field, "verbose_name", fallback_label or name)),
        kind=kind,
        is_groupable=is_groupable,
        is_user_relation=is_user_relation,
        is_nullable=bool(getattr(model_field, "null", False)),
        related_model_name=related_model.__name__ if related_model else "",
        label_orm_path=label_orm_path,
        label_is_i18n_json=isinstance(label_field, models.JSONField),
        label_is_text=isinstance(label_field, (models.CharField, models.TextField)),
    )


def _is_scalar_column(model_field) -> bool:
    """Reverse and many-to-many relations have no single value on the row."""
    return (
        getattr(model_field, "concrete", False)
        and not model_field.many_to_many
        and not model_field.one_to_many
    )


def _facets_for(model_field, allow_current_user: bool = True) -> Dict[str, Any]:
    """
    Facet rows applying to this field, keyed by operator.

    Matched by isinstance against each row's field_class, most specific first,
    so a subclass beats its base. A current-user operand only makes sense on a
    relation to the user model.
    """
    facets: Dict[str, Any] = {}

    for facet in sorted(_resource_field_facets(), key=lambda row: row.sortorder):
        if not allow_current_user and CURRENT_USER_FORMAT in (
            facet.param_formats or []
        ):
            continue
        field_class = _import_field_class(facet.field_class)
        if field_class is not None and isinstance(model_field, field_class):
            facets.setdefault(facet.operator, facet)

    return facets


def _is_groupable(model_field) -> bool:
    """Groupable when the domain is bounded; a timestamp or key is not."""
    return bool(
        model_field.many_to_one
        or model_field.one_to_one
        or model_field.choices
        or isinstance(model_field, models.BooleanField)
    )


def _choice_enumerable_models() -> frozenset:
    return frozenset(
        getattr(
            settings,
            "RESOURCE_FIELD_CHOICE_ENUMERABLE_MODELS",
            DEFAULT_CHOICE_ENUMERABLE_MODELS,
        )
    )


def _label_field_for(related_model):
    """
    The one field of a related model reachable by a single hop.

    Anything that is not the label field is unreachable, which is what keeps
    auth.User's credential and privilege columns out of the search surface.
    """
    if related_model is None:
        return None, None

    for label_name in LABEL_FIELD_CANDIDATES:
        try:
            return label_name, related_model._meta.get_field(label_name)
        except FieldDoesNotExist:
            continue
    return None, None


@lru_cache(maxsize=1)
def _resource_field_facets() -> Tuple[Any, ...]:
    from arches_search.models.models import ResourceFieldFacet

    return tuple(ResourceFieldFacet.objects.all())


@lru_cache(maxsize=None)
def _import_field_class(dotted_path: str) -> Optional[type]:
    try:
        imported = import_string(dotted_path)
    except ImportError:
        return None
    return imported if isinstance(imported, type) else None


@lru_cache(maxsize=1)
def get_resource_instance_fields() -> ResourceInstanceFieldRegistry:
    """Process-wide registry. The model layout cannot change at runtime."""
    return ResourceInstanceFieldRegistry()
