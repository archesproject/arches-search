import io
import uuid
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from arches.app.models.models import (
    DValueType,
    GraphModel,
    Language,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)

from arches_controlled_lists.models import List, ListItem, ListItemValue

# python manage.py test tests.test_term_suggestions --settings="tests.test_settings"


class TermSuggestionViewTests(TestCase):
    """Characterization tests for TermSuggestionView, written against its
    current (pre-refactor) implementation so they can be re-run unchanged
    against the util-extracted version to confirm behavior is preserved."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="term_suggestion_admin",
            password="password123",
            email="term_suggestion_admin@example.com",
        )

        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Term Suggestion Test Graph",
            slug="term-suggestion-test-graph",
            isresource=True,
            is_active=True,
            iconclass="fa fa-flask",
        )

        # --- string-datatype fixture ---
        cls.string_nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.string_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="term_test_string",
            alias="term_test_string",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.string_nodegroup,
            istopnode=True,
        )
        cls.string_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
        )
        cls.string_tile = TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.string_nodegroup,
            resourceinstance=cls.string_resource,
            data={
                str(cls.string_node.nodeid): {
                    "en": {"value": "zephyrblue mineral sample", "direction": "ltr"},
                },
            },
            provisionaledits=None,
        )

        # --- reference-datatype fixture ---
        cls.reference_nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.reference_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="term_test_reference",
            alias="term_test_reference",
            datatype="reference",
            graph=cls.graph,
            nodegroup=cls.reference_nodegroup,
            istopnode=True,
        )

        # List.save() unconditionally calls delete_index() (an ES call) even
        # when searchable=False (the default here). arches_search's settings
        # don't define REFERENCES_INDEX_NAME (that's an arches_controlled_lists
        # concern this project doesn't need), so that ES sync side effect is
        # muted here -- irrelevant to what TermSuggestionView reads (which
        # comes entirely from Postgres via ListView's serialize()).
        with mock.patch.object(List, "delete_index"):
            cls.controlled_list = List.objects.create(name="Rock Types")
        cls.pref_label_type = DValueType.objects.get(valuetype="prefLabel")
        cls.english = Language.objects.get(code="en")

        cls.list_item = ListItem.objects.create(
            id=uuid.uuid4(),
            list=cls.controlled_list,
            sortorder=0,
            uri="https://example.org/controlled-lists/quartzite-formation",
        )
        cls.list_item_value = ListItemValue.objects.create(
            id=uuid.uuid4(),
            list_item=cls.list_item,
            valuetype=cls.pref_label_type,
            language=cls.english,
            value="Quartzite Formation",
        )

        cls.reference_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
        )
        cls.reference_tile = TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=cls.reference_nodegroup,
            resourceinstance=cls.reference_resource,
            data={
                str(cls.reference_node.nodeid): [
                    {
                        "uri": cls.list_item.uri,
                        "list_id": str(cls.controlled_list.id),
                        "labels": [
                            {
                                "id": str(cls.list_item_value.id),
                                "value": "Quartzite Formation",
                                "language_id": "en",
                                "valuetype_id": "prefLabel",
                                "list_item_id": str(cls.list_item.id),
                            }
                        ],
                    }
                ],
            },
            provisionaledits=None,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def _reindex(self):
        call_command("arches_search", "reindex_database", stdout=io.StringIO())

    def test_empty_query_returns_empty_results_with_no_db_query(self):
        response = self.client.get(reverse("term_suggestion_search"), {"q": ""})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})

    def test_missing_query_returns_empty_results(self):
        response = self.client.get(reverse("term_suggestion_search"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})

    def test_substring_match_on_string_datatype_term(self):
        self._reindex()

        response = self.client.get(
            reverse("term_suggestion_search"), {"q": "zephyrblue"}
        )

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        matches = [r for r in results if r["text"] == "zephyrblue mineral sample"]
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match["datatype"], "string")
        self.assertEqual(
            match["resourceinstanceid"], str(self.string_resource.resourceinstanceid)
        )
        self.assertEqual(match["addtional_info"], {})
        self.assertEqual(match["graph_icon"], "fa fa-flask")
        self.assertEqual(match["graph_name"], "Term Suggestion Test Graph")

    def test_reference_datatype_match_includes_item_path(self):
        self._reindex()

        response = self.client.get(
            reverse("term_suggestion_search"), {"q": "Quartzite"}
        )

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        matches = [r for r in results if r["text"] == "Quartzite Formation"]
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match["datatype"], "reference")
        self.assertEqual(
            match["addtional_info"]["path"],
            ["Rock Types", "Quartzite Formation"],
        )

    def test_reference_match_is_not_crowded_out_by_common_substring(self):
        """Bucketing check: a substring popular among plain-term rows must not
        push a matching reference-datatype row out of the results. MAX_RESULTS
        is patched down to a small number so a handful of incidental string
        matches is enough to exceed the non-reference bucket's cap, while the
        single reference match (in its own bucket) is unaffected."""
        shared_substring = "credaceous"
        incidental_string_values = [
            f"{shared_substring}-{suffix}"
            for suffix in ("alpha", "bravo", "charlie", "delta", "echo")
        ]

        for value in incidental_string_values:
            resource = ResourceInstance.objects.create(
                resourceinstanceid=uuid.uuid4(),
                graph=self.graph,
            )
            TileModel.objects.create(
                tileid=uuid.uuid4(),
                nodegroup=self.string_nodegroup,
                resourceinstance=resource,
                data={
                    str(self.string_node.nodeid): {
                        "en": {"value": value, "direction": "ltr"},
                    },
                },
                provisionaledits=None,
            )

        reference_list_item = ListItem.objects.create(
            id=uuid.uuid4(),
            list=self.controlled_list,
            sortorder=1,
            uri="https://example.org/controlled-lists/credaceous-schist",
        )
        reference_list_item_value = ListItemValue.objects.create(
            id=uuid.uuid4(),
            list_item=reference_list_item,
            valuetype=self.pref_label_type,
            language=self.english,
            value=f"{shared_substring} schist",
        )
        reference_resource = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=self.graph,
        )
        TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=self.reference_nodegroup,
            resourceinstance=reference_resource,
            data={
                str(self.reference_node.nodeid): [
                    {
                        "uri": reference_list_item.uri,
                        "list_id": str(self.controlled_list.id),
                        "labels": [
                            {
                                "id": str(reference_list_item_value.id),
                                "value": f"{shared_substring} schist",
                                "language_id": "en",
                                "valuetype_id": "prefLabel",
                                "list_item_id": str(reference_list_item.id),
                            }
                        ],
                    }
                ],
            },
            provisionaledits=None,
        )

        self._reindex()

        # Patched well below the 5 incidental string matches, so the
        # non-reference bucket alone would drop some of them -- proving the
        # reference bucket (only 1 candidate) is scanned independently.
        with mock.patch("arches_search.utils.term_search.suggestions.MAX_RESULTS", 3):
            response = self.client.get(
                reverse("term_suggestion_search"), {"q": shared_substring}
            )

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]

        non_reference_matches = [r for r in results if r["datatype"] == "string"]
        self.assertLessEqual(len(non_reference_matches), 3)

        reference_matches = [
            r for r in results if r["text"] == f"{shared_substring} schist"
        ]
        self.assertEqual(len(reference_matches), 1)
        self.assertEqual(reference_matches[0]["datatype"], "reference")
