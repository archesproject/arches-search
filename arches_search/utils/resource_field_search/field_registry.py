"""
Discovery of the ResourceInstance system-level fields that search can filter,
sort, and group by.

The set of queryable fields is *derived from the model*, not maintained by hand:
every concrete field on ResourceInstance whose Django field class has a known
operator vocabulary becomes queryable automatically. If Arches core adds a new
scalar or foreign-key column to ResourceInstance, it becomes usable here with no
change to this app. Conversely, field classes with no entry in
FIELD_CLASS_OPERATORS (e.g. JSONField, and therefore Arches' I18n_TextField,
which subclasses it) simply never appear -- no name-based denylist is needed.

Related models are reachable exactly one hop, and only via their *label* field
(``username`` for the user model, ``name`` otherwise). That rule is what keeps
sensitive columns such as ``principaluser__password`` or
``principaluser__is_superuser`` unreachable: they are not label fields, so no
descriptor is ever generated for them and the resolver has nothing to look up.
Reachability is therefore closed by construction rather than by blocklist.
"""

from dataclasses import dataclass, field as dataclass_field
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import models

from arches.app.models.models import ResourceInstance

OPERATOR_EQUALS = "EQUALS"
OPERATOR_IN = "IN"
OPERATOR_CONTAINS = "CONTAINS"
OPERATOR_STARTS_WITH = "STARTS_WITH"
OPERATOR_RANGE = "RANGE"
OPERATOR_BEFORE = "BEFORE"
OPERATOR_AFTER = "AFTER"
OPERATOR_IS_TRUE = "IS_TRUE"
OPERATOR_IS_FALSE = "IS_FALSE"
OPERATOR_HAS_ANY_VALUE = "HAS_ANY_VALUE"
OPERATOR_HAS_NO_VALUE = "HAS_NO_VALUE"
OPERATOR_IS_CURRENT_USER = "IS_CURRENT_USER"
OPERATOR_IS_NOT_CURRENT_USER = "IS_NOT_CURRENT_USER"

# Operators that take no operand. Supplying a value alongside one of these is a
# validation error rather than a silently ignored no-op, so that an attempt to
# smuggle a user id into IS_CURRENT_USER fails loudly.
ZERO_ARITY_OPERATORS = frozenset(
    {
        OPERATOR_IS_TRUE,
        OPERATOR_IS_FALSE,
        OPERATOR_HAS_ANY_VALUE,
        OPERATOR_HAS_NO_VALUE,
        OPERATOR_IS_CURRENT_USER,
        OPERATOR_IS_NOT_CURRENT_USER,
    }
)

_PRESENCE_OPERATORS = (OPERATOR_HAS_ANY_VALUE, OPERATOR_HAS_NO_VALUE)

# Django field class -> supported operators. Evaluated in order, first
# isinstance() match wins, so more specific classes must precede their bases
# (DateTimeField subclasses DateField; JSONField is deliberately absent).
FIELD_CLASS_OPERATORS: Tuple[Tuple[type, Tuple[str, ...]], ...] = (
    (models.BooleanField, (OPERATOR_IS_TRUE, OPERATOR_IS_FALSE)),
    (models.ForeignKey, (OPERATOR_EQUALS, OPERATOR_IN) + _PRESENCE_OPERATORS),
    (models.UUIDField, (OPERATOR_EQUALS, OPERATOR_IN) + _PRESENCE_OPERATORS),
    (
        models.DateTimeField,
        (OPERATOR_EQUALS, OPERATOR_RANGE, OPERATOR_BEFORE, OPERATOR_AFTER)
        + _PRESENCE_OPERATORS,
    ),
    (
        models.DateField,
        (OPERATOR_EQUALS, OPERATOR_RANGE, OPERATOR_BEFORE, OPERATOR_AFTER)
        + _PRESENCE_OPERATORS,
    ),
    (
        models.TextField,
        (OPERATOR_EQUALS, OPERATOR_CONTAINS, OPERATOR_STARTS_WITH)
        + _PRESENCE_OPERATORS,
    ),
    (
        models.CharField,
        (OPERATOR_EQUALS, OPERATOR_CONTAINS, OPERATOR_STARTS_WITH)
        + _PRESENCE_OPERATORS,
    ),
)

# Field classes whose cardinality is naturally bounded, and which are therefore
# meaningful to group by. Grouping on a timestamp or a primary key would produce
# roughly one bucket per row.
GROUPABLE_FIELD_CLASSES: Tuple[type, ...] = (models.ForeignKey, models.BooleanField)

# Coarse widget hint for clients, so a UI can pick an input without needing to
# know Django's field classes. Ordered like FIELD_CLASS_OPERATORS: first match
# wins.
KIND_USER = "USER"
KIND_CHOICE = "CHOICE"
KIND_BOOLEAN = "BOOLEAN"
KIND_DATE = "DATE"
KIND_ID = "ID"
KIND_TEXT = "TEXT"

FIELD_CLASS_KINDS: Tuple[Tuple[type, str], ...] = (
    (models.BooleanField, KIND_BOOLEAN),
    (models.ForeignKey, KIND_CHOICE),
    (models.UUIDField, KIND_ID),
    (models.DateTimeField, KIND_DATE),
    (models.DateField, KIND_DATE),
    (models.TextField, KIND_TEXT),
    (models.CharField, KIND_TEXT),
)

# The single field of a related model that one hop may reach.
USER_LABEL_FIELD = "username"
DEFAULT_LABEL_FIELD = "name"


@dataclass(frozen=True)
class ResourceFieldDescriptor:
    """One queryable field, as exposed to clients."""

    name: str
    orm_path: str
    operators: Tuple[str, ...]
    label: str = ""
    kind: str = ""
    is_groupable: bool = False
    is_user_relation: bool = False
    # For foreign keys: where the human-readable label lives, so sorting can
    # order by label rather than by an opaque primary key.
    label_orm_path: Optional[str] = None
    label_is_i18n_json: bool = False
    label_is_text: bool = False
    metadata: Dict[str, Any] = dataclass_field(default_factory=dict)

    def supports(self, operator: str) -> bool:
        return operator in self.operators


def _operators_for_field(model_field) -> Tuple[str, ...]:
    for field_class, operators in FIELD_CLASS_OPERATORS:
        if isinstance(model_field, field_class):
            return operators
    return ()


def _is_groupable(model_field) -> bool:
    return isinstance(model_field, GROUPABLE_FIELD_CLASSES)


def _kind_for_field(model_field, is_user_relation: bool) -> str:
    if is_user_relation:
        return KIND_USER
    for field_class, kind in FIELD_CLASS_KINDS:
        if isinstance(model_field, field_class):
            return kind
    return ""


def _label_field_for(related_model):
    """
    The one field of a related model reachable by a single hop.

    Returns (field_name, model_field) or (None, None). Anything that is not the
    designated label field is unreachable, which is what keeps auth.User's
    credential and privilege columns out of the search surface entirely.
    """
    if related_model is None:
        return None, None

    label_name = (
        USER_LABEL_FIELD if related_model is get_user_model() else DEFAULT_LABEL_FIELD
    )
    try:
        return label_name, related_model._meta.get_field(label_name)
    except Exception:
        return None, None


class ResourceFieldRegistry:
    """
    The single source of truth for which resource fields are queryable.

    Filtering, sorting, grouping, and the metadata endpoint all resolve against
    this same registry, so the four cannot drift apart.
    """

    def __init__(self, model=ResourceInstance) -> None:
        self.model = model
        self._descriptors: Dict[str, ResourceFieldDescriptor] = self._discover()

    def _discover(self) -> Dict[str, ResourceFieldDescriptor]:
        descriptors: Dict[str, ResourceFieldDescriptor] = {}

        for model_field in self.model._meta.get_fields():
            # Reverse relations and many-to-many have no single scalar value on
            # the row being searched.
            if not getattr(model_field, "concrete", False):
                continue
            if model_field.many_to_many or model_field.one_to_many:
                continue

            operators = _operators_for_field(model_field)
            if not operators:
                continue

            is_relation = bool(model_field.many_to_one or model_field.one_to_one)
            related_model = model_field.related_model if is_relation else None
            is_user_relation = is_relation and related_model is get_user_model()

            if is_user_relation:
                operators = operators + (
                    OPERATOR_IS_CURRENT_USER,
                    OPERATOR_IS_NOT_CURRENT_USER,
                )

            label_name, label_field = _label_field_for(related_model)
            label_orm_path = f"{model_field.name}__{label_name}" if label_name else None

            descriptors[model_field.name] = ResourceFieldDescriptor(
                name=model_field.name,
                label=str(getattr(model_field, "verbose_name", model_field.name)),
                kind=_kind_for_field(model_field, is_user_relation),
                # attname gives "principaluser_id" for a FK, so an EQUALS/IN
                # compares raw key values without a join.
                orm_path=model_field.attname,
                operators=operators,
                is_groupable=_is_groupable(model_field),
                is_user_relation=is_user_relation,
                label_orm_path=label_orm_path,
                label_is_i18n_json=isinstance(label_field, models.JSONField),
                label_is_text=isinstance(
                    label_field, (models.CharField, models.TextField)
                ),
                metadata=(
                    {"related_model": related_model.__name__} if related_model else {}
                ),
            )

            # The one permitted hop: the related model's label field.
            if label_orm_path and label_field is not None:
                label_operators = _operators_for_field(label_field)
                if label_operators:
                    descriptors[label_orm_path] = ResourceFieldDescriptor(
                        name=label_orm_path,
                        label=str(getattr(label_field, "verbose_name", label_name)),
                        kind=_kind_for_field(label_field, False),
                        orm_path=label_orm_path,
                        operators=label_operators,
                        is_groupable=False,
                        is_user_relation=is_user_relation,
                        metadata={"related_model": related_model.__name__},
                    )

        return descriptors

    def get(self, field_name: str) -> Optional[ResourceFieldDescriptor]:
        return self._descriptors.get(field_name)

    def names(self) -> Tuple[str, ...]:
        return tuple(sorted(self._descriptors))

    def all(self) -> Tuple[ResourceFieldDescriptor, ...]:
        return tuple(self._descriptors[name] for name in self.names())

    def groupable(self) -> Tuple[ResourceFieldDescriptor, ...]:
        return tuple(descriptor for descriptor in self.all() if descriptor.is_groupable)


@lru_cache(maxsize=1)
def get_resource_field_registry() -> ResourceFieldRegistry:
    """Process-wide registry. The model layout cannot change at runtime."""
    return ResourceFieldRegistry()
