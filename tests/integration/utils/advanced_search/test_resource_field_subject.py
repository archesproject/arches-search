"""
Integration tests for the RESOURCE_FIELD subject type.

A RESOURCE_FIELD subject addresses a column on the resource row itself --
its lifecycle state, its creator, when it was made -- rather than a value in a
tile. It therefore names no graph and no node, needs none of the correlated
subquery machinery a node subject does, and compiles to a plain predicate.

Sibling of test_search_models_subject.py: same shape of coverage, for the third
of the three subject types.

Covers:
  - Subject shape, settled without touching the database.
  - Field and operator, settled against ResourceInstanceFieldRegistry as the
    clause compiles, including that IS_CURRENT_USER carrying an operand is
    rejected rather than silently ignored.
  - Every operator's compiled ORM predicate, and the operand shapes each
    accepts.
  - Behavior against real rows, including the AnonymousUser case and the
    guarantee that such a clause can only narrow what permissions already allow.
  - Where the clause may appear: nested groups and both sides of a relationship,
    but not TILE scope and not a RELATED clause.

python manage.py test tests.integration.utils.advanced_search.test_resource_field_subject --settings="tests.test_settings"
"""

import uuid

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.test import SimpleTestCase, TestCase
from django.utils import translation

from arches.app.models.models import ResourceInstance
from arches.app.utils.permission_backend import assign_perm

from arches_search.utils.search import SearchCompiler, SearchPayload
from arches_search.utils.advanced_search.clause_evaluation.resource_field_clause_evaluator import (
    ResourceFieldClauseEvaluator,
)
from arches_search.utils.advanced_search.advanced_search import (
    AdvancedSearchQueryCompiler,
)
from arches_search.utils.advanced_search.payload_validator import PayloadValidator
from arches_search.utils.resource_field_search.field_registry import (
    get_resource_instance_fields,
)

from tests.integration.utils.advanced_search.test_advanced_search import (
    AdvancedSearchSetupMixin,
    DOG_A_ID,
    PERSON_A_ID,
    PERSON_B_ID,
    PERSON_C_ID,
)
from tests.test_resource_field_search import (
    OPERATOR_AFTER,
    OPERATOR_BEFORE,
    OPERATOR_CONTAINS,
    OPERATOR_EQUALS,
    OPERATOR_HAS_ANY_VALUE,
    OPERATOR_HAS_NO_VALUE,
    OPERATOR_IN,
    OPERATOR_IS_CURRENT_USER,
    OPERATOR_IS_NOT_CURRENT_USER,
    OPERATOR_RANGE,
    OPERATOR_STARTS_WITH,
    ResourceFieldFixtureMixin,
    advanced_search_query,
    resource_field_clause,
)


class ResourceFieldSubjectStructureTests(SimpleTestCase):
    """
    The payload validator settles shape only, and does so without the database.

    Running these without one is the assertion: if a registry lookup ever moves
    into the validator, these fail rather than silently adding a query to every
    search.
    """

    def _validate(self, subject):
        PayloadValidator().validate(
            advanced_search_query(
                "any-slug",
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": subject,
                    "operator": OPERATOR_EQUALS,
                    "operands": [{"type": "LITERAL", "value": "x"}],
                },
            )
        )

    def test_field_subject_is_accepted(self):
        self._validate({"type": "RESOURCE_FIELD", "field": "legacyid"})

    def test_field_must_be_a_non_empty_string(self):
        for field in ("", None, 5):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    self._validate({"type": "RESOURCE_FIELD", "field": field})

    def test_missing_field_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._validate({"type": "RESOURCE_FIELD"})

    def test_node_addressing_is_rejected_on_a_field_subject(self):
        with self.assertRaises(ValidationError):
            self._validate(
                {
                    "type": "RESOURCE_FIELD",
                    "field": "legacyid",
                    "graph_slug": "x",
                    "node_alias": "y",
                    "search_models": [],
                }
            )


class ResourceFieldClauseValidationTests(TestCase):
    """
    Field and operator are settled against the registry as the clause compiles,
    which is where the database is available.
    """

    def _build(self, field, operator, *operand_values, user=AnonymousUser()):
        return ResourceFieldClauseEvaluator(user=user).build_predicate(
            resource_field_clause(field, operator, *operand_values)
        )

    def test_unknown_field_raises(self):
        with self.assertRaises(ValidationError):
            self._build("not_a_field", OPERATOR_EQUALS, 1)

    def test_sensitive_field_raises(self):
        with self.assertRaises(ValidationError):
            self._build("principaluser__password", OPERATOR_EQUALS, "x")

    def test_operator_not_supported_for_field_raises(self):
        with self.assertRaises(ValidationError):
            self._build("createdtime", OPERATOR_CONTAINS, "x")

    def test_is_current_user_rejects_supplied_operand(self):
        # Supplying one is an attempt to filter as somebody else.
        with self.assertRaises(ValidationError):
            self._build("principaluser", OPERATOR_IS_CURRENT_USER, 1)

    def test_is_current_user_without_operand_is_valid(self):
        self._build("principaluser", OPERATOR_IS_CURRENT_USER)

    def test_missing_operand_raises(self):
        with self.assertRaises(ValidationError):
            self._build("legacyid", OPERATOR_EQUALS)

    def test_a_quantifier_other_than_any_is_rejected(self):
        """
        A resource field holds one value, so ALL and NONE have nothing to
        quantify over. Ignoring them would hand back the opposite result set
        without a word -- NONE reads as a negation.
        """
        for quantifier in ("ALL", "NONE"):
            with self.subTest(quantifier=quantifier):
                clause = resource_field_clause(
                    "principaluser", OPERATOR_IS_CURRENT_USER
                )
                clause["quantifier"] = quantifier
                with self.assertRaises(ValidationError):
                    PayloadValidator().validate(
                        advanced_search_query("any-slug", clause)
                    )

    def test_a_nested_group_cannot_smuggle_one_into_tile_scope(self):
        """
        The rejection applies per group: validation recurses into subgroups,
        and each carries its own scope.
        """
        inner = advanced_search_query(
            "any-slug", resource_field_clause("legacyid", OPERATOR_EQUALS, "x")
        )
        inner["scope"] = "TILE"
        outer = advanced_search_query("any-slug")
        outer["groups"] = [inner]

        with self.assertRaises(ValidationError):
            AdvancedSearchQueryCompiler(outer).compile(
                pre_filter=ResourceInstance.objects.none()
            )

    def test_resource_field_clause_is_rejected_under_tile_scope(self):
        # A resource field is a column on the resource, not a value in a tile.
        tile_scoped = advanced_search_query(
            "any-slug", resource_field_clause("legacyid", OPERATOR_EQUALS, "x")
        )
        tile_scoped["scope"] = "TILE"
        with self.assertRaises(ValidationError):
            AdvancedSearchQueryCompiler(tile_scoped).compile(
                pre_filter=ResourceInstance.objects.none()
            )


class ResourceFieldPredicateTests(TestCase):
    """
    Each operator compiles to the ORM predicate it claims to.

    The whole operator vocabulary is checked here rather than paying for a
    fixture per operator.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.registry = get_resource_instance_fields()

    def _predicate(self, field, operator, *operand_values, user=AnonymousUser()):
        return ResourceFieldClauseEvaluator(
            user=user, registry=self.registry
        ).build_predicate(resource_field_clause(field, operator, *operand_values))

    def test_scalar_operators_compile_to_expected_lookups(self):
        cases = [
            (OPERATOR_EQUALS, "legacyid", ("abc",), Q(legacyid="abc")),
            (OPERATOR_IN, "legacyid", (["a", "b"],), Q(legacyid__in=["a", "b"])),
            (OPERATOR_CONTAINS, "legacyid", ("ab",), Q(legacyid__icontains="ab")),
            (OPERATOR_STARTS_WITH, "legacyid", ("ab",), Q(legacyid__istartswith="ab")),
        ]
        for operator, field, operands, expected in cases:
            with self.subTest(operator=operator):
                self.assertEqual(self._predicate(field, operator, *operands), expected)

    def test_date_operators_compile_to_expected_lookups(self):
        cases = [
            (
                OPERATOR_RANGE,
                ("2020-01-01", "2020-12-31"),
                Q(createdtime__range=("2020-01-01", "2020-12-31")),
            ),
            (OPERATOR_BEFORE, ("2020-01-01",), Q(createdtime__lt="2020-01-01")),
            (OPERATOR_AFTER, ("2020-01-01",), Q(createdtime__gt="2020-01-01")),
        ]
        for operator, operands, expected in cases:
            with self.subTest(operator=operator):
                self.assertEqual(
                    self._predicate("createdtime", operator, *operands), expected
                )

    def test_i18n_text_operators_key_on_the_active_language(self):
        """name is stored as {language: value}, so the lookup carries the language."""
        with translation.override("en"):
            self.assertEqual(
                self._predicate("name", OPERATOR_CONTAINS, "bronze"),
                Q(name__en__icontains="bronze"),
            )

    def test_presence_operators_compile_to_isnull_lookups(self):
        self.assertEqual(
            self._predicate("principaluser", OPERATOR_HAS_ANY_VALUE),
            ~Q(principaluser_id__isnull=True),
        )
        self.assertEqual(
            self._predicate("principaluser", OPERATOR_HAS_NO_VALUE),
            Q(principaluser_id__isnull=True),
        )

    def test_is_not_current_user_is_a_plain_negation(self):
        """
        No isnull clause is needed to keep creator-less rows: Django compiles a
        negated lookup to NOT (col = x AND col IS NOT NULL), which already keeps
        them. ResourceFieldClauseFilteringTests asserts that behaviour on rows.
        """
        user = User(id=42, username="someone")
        predicate = self._predicate(
            "principaluser", OPERATOR_IS_NOT_CURRENT_USER, user=user
        )

        self.assertEqual(predicate, ~Q(principaluser_id=42))

    def test_anonymous_is_not_current_user_constrains_nothing(self):
        """
        There is no identity to exclude, so the clause must not narrow -- and it
        has to say so with a predicate true for every row. An empty Q() would be
        absorbed when combined, turning "everything" into "nothing" under OR.
        """
        self.assertEqual(
            self._predicate("principaluser", OPERATOR_IS_NOT_CURRENT_USER),
            ~Q(pk__in=[]),
        )


class ResourceFieldOperandShapeTests(TestCase):
    """
    Each operator rejects a malformed operand rather than passing it to the ORM.

    A bad shape that reaches the query layer surfaces as a 500 (or, worse, a
    silently wrong result set), so these are 400s raised up front.
    """

    def _assert_rejected(self, operator, field, *operand_values):
        with self.assertRaises(ValidationError):
            ResourceFieldClauseEvaluator(user=AnonymousUser()).build_predicate(
                resource_field_clause(field, operator, *operand_values)
            )

    def _assert_accepted(self, operator, field, *operand_values):
        ResourceFieldClauseEvaluator(user=AnonymousUser()).build_predicate(
            resource_field_clause(field, operator, *operand_values)
        )

    def test_in_requires_a_non_empty_list(self):
        # A relation field: IN is only offered for FK/UUID fields.
        field = "resource_instance_lifecycle_state"
        for value in ([], "not-a-list", None):
            with self.subTest(value=value):
                self._assert_rejected(OPERATOR_IN, field, value)
        self._assert_accepted(OPERATOR_IN, field, [str(uuid.uuid4())])

    def test_range_requires_both_bounds(self):
        for operands in (("2020-01-01",), (), ("2020-01-01", None)):
            with self.subTest(operands=operands):
                self._assert_rejected(OPERATOR_RANGE, "createdtime", *operands)
        self._assert_accepted(OPERATOR_RANGE, "createdtime", "2020-01-01", "2020-12-31")

    def test_text_operators_require_a_non_empty_string(self):
        for operator in (OPERATOR_CONTAINS, OPERATOR_STARTS_WITH):
            for value in ("", ["a"], 5):
                with self.subTest(operator=operator, value=value):
                    self._assert_rejected(operator, "legacyid", value)
            self._assert_accepted(operator, "legacyid", "ab")

    def test_single_value_operators_reject_collections(self):
        for operator in (OPERATOR_EQUALS, OPERATOR_BEFORE, OPERATOR_AFTER):
            for value in (["a"], {"from": "x"}):
                with self.subTest(operator=operator, value=value):
                    self._assert_rejected(operator, "createdtime", value)


class ResourceFieldClauseFilteringTests(ResourceFieldFixtureMixin, TestCase):
    def _filtered_ids(self, user, *clauses):
        evaluator = ResourceFieldClauseEvaluator(user=user)
        predicate = Q()
        for clause in clauses:
            predicate &= evaluator.build_predicate(clause)
        return set(
            ResourceInstance.objects.filter(graph=self.graph)
            .filter(predicate)
            .values_list("resourceinstanceid", flat=True)
        )

    def _payload_for(self, *clauses):
        return SearchPayload(
            graph_slugs=[self.graph.slug],
            term_search=None,
            advanced_search_queries=[advanced_search_query(self.graph.slug, *clauses)],
        )

    def test_is_current_user_returns_only_own_resources(self):
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                resource_field_clause("principaluser", OPERATOR_IS_CURRENT_USER),
            ),
            {self.owned_draft.pk, self.owned_submitted.pk},
        )

    def test_is_current_user_matches_nothing_for_anonymous(self):
        # AnonymousUser.id is None; a naive equality filter would compile to
        # "principaluser_id IS NULL" and surface every creator-less resource.
        self.assertEqual(
            self._filtered_ids(
                AnonymousUser(),
                resource_field_clause("principaluser", OPERATOR_IS_CURRENT_USER),
            ),
            set(),
        )

    def test_is_not_current_user_includes_creatorless_resources(self):
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                resource_field_clause("principaluser", OPERATOR_IS_NOT_CURRENT_USER),
            ),
            {self.other_draft.pk, self.unowned.pk},
        )

    def test_filter_by_username_hop(self):
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                resource_field_clause(
                    "principaluser__username", OPERATOR_EQUALS, "rf_other"
                ),
            ),
            {self.other_draft.pk},
        )

    def test_filter_by_lifecycle_state_in(self):
        self.assertEqual(
            self._filtered_ids(
                self.owner,
                resource_field_clause(
                    "resource_instance_lifecycle_state",
                    OPERATOR_IN,
                    [str(self.state_submitted.pk)],
                ),
            ),
            {self.owned_submitted.pk},
        )

    def test_clauses_combine_with_or(self):
        # Compiled without the permission layer, so this is about OR alone.
        query = advanced_search_query(
            self.graph.slug,
            resource_field_clause(
                "principaluser__username", OPERATOR_EQUALS, "rf_other"
            ),
            resource_field_clause("principaluser", OPERATOR_HAS_NO_VALUE),
            logic="OR",
        )
        matched = set(
            AdvancedSearchQueryCompiler(query, user=self.owner)
            .compile(pre_filter=ResourceInstance.objects.filter(graph=self.graph))
            .values_list("resourceinstanceid", flat=True)
        )
        self.assertEqual(matched, {self.other_draft.pk, self.unowned.pk})

    def test_constraining_nothing_does_not_empty_an_or_group(self):
        """
        An anonymous "is not me" constrains nothing, which under OR must mean
        "everything". Spelled as an empty Q it would be absorbed when combined,
        turning the whole group into "match nothing" -- the opposite.
        """
        query = advanced_search_query(
            self.graph.slug,
            resource_field_clause("principaluser", OPERATOR_IS_NOT_CURRENT_USER),
            resource_field_clause(
                "resource_instance_lifecycle_state", OPERATOR_IN, [str(uuid.uuid4())]
            ),
            logic="OR",
        )
        matched = set(
            AdvancedSearchQueryCompiler(query, user=AnonymousUser())
            .compile(pre_filter=ResourceInstance.objects.filter(graph=self.graph))
            .values_list("resourceinstanceid", flat=True)
        )

        every_resource = set(
            ResourceInstance.objects.filter(graph=self.graph).values_list(
                "resourceinstanceid", flat=True
            )
        )
        self.assertEqual(matched, every_resource)

    def test_filter_cannot_surface_resources_the_user_cannot_see(self):
        """
        A resource-field clause only narrows; the permission framework remains
        the authority on what is visible.
        """
        payload = self._payload_for(
            resource_field_clause(
                "principaluser__username", OPERATOR_EQUALS, "rf_owner"
            )
        )
        visible = set(
            SearchCompiler(payload, self.member)
            .compile()
            .results.values_list("resourceinstanceid", flat=True)
        )
        self.assertEqual(visible, set())

        owner_visible = set(
            SearchCompiler(payload, self.owner)
            .compile()
            .results.values_list("resourceinstanceid", flat=True)
        )
        self.assertEqual(owner_visible, {self.owned_draft.pk, self.owned_submitted.pk})

    def test_granted_resource_still_requires_the_clause_to_match(self):
        assign_perm("view_resourceinstance", self.group, self.other_draft)
        payload = self._payload_for(
            resource_field_clause(
                "resource_instance_lifecycle_state",
                OPERATOR_IN,
                [str(self.state_submitted.pk)],
            )
        )
        visible = set(
            SearchCompiler(payload, self.member)
            .compile()
            .results.values_list("resourceinstanceid", flat=True)
        )
        # other_draft is visible to member but is not in the requested state.
        self.assertEqual(visible, set())


class ResourceFieldClausePlacementTests(AdvancedSearchSetupMixin, TestCase):
    """
    A resource field clause is an ordinary clause, so it has to work everywhere
    an ordinary clause works -- nested in a subgroup, and on either side of a
    relationship. The Person/Dog fixture is used because it is the only one with
    real relationships.

    person_a and dog_a are owned; person_b and person_c are the only people with
    pets, and person_b's pet is the owned dog.
    """

    PETS_RELATIONSHIP = {
        "path": {"type": "NODE", "graph_slug": "person", "node_alias": "pets"},
        "is_inverse": False,
        "traversal_quantifier": "ANY",
    }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.owner = User.objects.create_user(username="placement_owner", password="pw")
        ResourceInstance.objects.filter(
            resourceinstanceid__in=[PERSON_A_ID, DOG_A_ID]
        ).update(principaluser=cls.owner)

    def _matches(self, payload):
        return set(
            AdvancedSearchQueryCompiler(payload, user=self.owner)
            .compile(pre_filter=ResourceInstance.objects.all())
            .values_list("resourceinstanceid", flat=True)
        )

    @staticmethod
    def _group(clauses=None, groups=None, relationship=None, graph_slug="person"):
        return {
            "graph_slug": graph_slug,
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": clauses or [],
            "groups": groups or [],
            "aggregations": [],
            "relationship": relationship,
        }

    def test_works_nested_in_a_subgroup(self):
        nested = self._group(
            groups=[
                self._group(
                    [resource_field_clause("principaluser", OPERATOR_IS_CURRENT_USER)]
                )
            ]
        )
        self.assertEqual(self._matches(nested), {PERSON_A_ID, DOG_A_ID})

    def test_filters_the_anchor_side_of_a_relationship(self):
        # Only person_b and person_c have pets, and neither is owned -- so a
        # dropped clause would match both instead of none.
        baseline = self._matches(self._group(relationship=self.PETS_RELATIONSHIP))
        self.assertEqual(baseline, {PERSON_B_ID, PERSON_C_ID})

        owned_anchor = self._matches(
            self._group(
                [resource_field_clause("principaluser", OPERATOR_IS_CURRENT_USER)],
                relationship=self.PETS_RELATIONSHIP,
            )
        )
        self.assertEqual(owned_anchor, set())

        unowned_anchor = self._matches(
            self._group(
                [resource_field_clause("principaluser", OPERATOR_HAS_NO_VALUE)],
                relationship=self.PETS_RELATIONSHIP,
            )
        )
        self.assertEqual(unowned_anchor, {PERSON_B_ID, PERSON_C_ID})

    def test_filters_the_child_side_of_a_relationship(self):
        # "people whose pet I own" -- only person_b's pet is the owned dog.
        matched = self._matches(
            self._group(
                groups=[
                    self._group(
                        [
                            resource_field_clause(
                                "principaluser", OPERATOR_IS_CURRENT_USER
                            )
                        ],
                        graph_slug="dog",
                    )
                ],
                relationship=self.PETS_RELATIONSHIP,
            )
        )
        self.assertEqual(matched, {PERSON_B_ID})

    def test_combines_with_a_node_clause_under_or(self):
        node_clause = {
            "type": "LITERAL",
            "quantifier": "ANY",
            "subject": {
                "type": "NODE",
                "graph_slug": "person",
                "node_alias": "first_name",
                "search_models": [],
            },
            "operator": "LIKE",
            "operands": [{"type": "LITERAL", "value": "FOO"}],
        }
        either = self._group(
            [
                resource_field_clause("principaluser", OPERATOR_HAS_NO_VALUE),
                node_clause,
            ]
        )
        either["logic"] = "OR"
        matched = self._matches(either)

        # person_a is owned, so it can only arrive via the node clause.
        self.assertIn(PERSON_A_ID, matched)
        # dog_a is owned and has no first_name, so it satisfies neither side.
        self.assertNotIn(DOG_A_ID, matched)


class ResourceFieldRelatedClauseTests(SimpleTestCase):
    def test_related_clause_error_names_the_right_requirements(self):
        # The node-subject message would say "add a graph_slug" -- wrong advice.
        clause = resource_field_clause("principaluser", OPERATOR_IS_CURRENT_USER)
        clause["type"] = "RELATED"

        with self.assertRaises(ValidationError) as raised:
            PayloadValidator().validate(advanced_search_query("person", clause))

        message = str(raised.exception)
        self.assertIn("resource field subject", message)
        self.assertIn("RELATED", message)
        self.assertNotIn("graph_slug", message)
