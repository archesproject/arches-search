import json
import uuid
from dataclasses import replace
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.db import connection
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    ResourceInstanceLifecycle,
    ResourceInstanceLifecycleState,
    ResourceXResource,
)
from arches.app.utils.permission_backend import assign_perm

from arches_search.utils.readable_nodes import ReadableNodes
from arches_search.views.api import relationship_graph as graph_api
from arches_search.views.api.resource_descriptors import ResourceDescriptorsAPI


class RelationshipGraphInputTest(SimpleTestCase):
    def test_labels_only_send_uuids_to_older_arches(self):
        type_id = str(uuid.uuid4())
        values = {type_id, "", "http://example.test/related", "not-a-uuid"}
        with patch.object(
            graph_api,
            "get_resource_relationship_type_label",
            return_value={type_id: "Owns"},
        ) as labels:
            result = graph_api._relationship_type_labels(values)
        labels.assert_called_once_with([type_id])
        self.assertEqual(
            result,
            {
                type_id: "Owns",
                "": "",
                "http://example.test/related": "related",
                "not-a-uuid": "not-a-uuid",
            },
        )

    def test_no_label_query_for_blank_or_url_types(self):
        with patch.object(graph_api, "get_resource_relationship_type_label") as labels:
            self.assertEqual(graph_api._relationship_type_labels({""}), {"": ""})
            self.assertEqual(graph_api._relationship_type_labels(set()), {})
        labels.assert_not_called()

    def test_row_id_preserves_delimiters_in_type_and_blank_types(self):
        graph_id = uuid.uuid4()
        for type_id in ("", "http://example.test/a|b"):
            self.assertEqual(
                graph_api._parse_row_id(f"incoming|{type_id}|{graph_id}"),
                ("incoming", type_id, graph_id),
            )

    def test_invalid_row_ids_are_rejected(self):
        for row_id in (
            None,
            {},
            "",
            "outgoing",
            f"both||{uuid.uuid4()}",
            "incoming||bad",
        ):
            with self.subTest(row_id=row_id), self.assertRaises(ValueError):
                graph_api._parse_row_id(row_id)

    def test_invalid_selections_are_rejected(self):
        for body in (
            None,
            [],
            {},
            {"selections": []},
            {"selections": [{}]},
            {"selections": [{"resource_id": "bad", "row_ids": []}]},
            {"selections": [{"resource_id": str(uuid.uuid4()), "row_ids": "bad"}]},
            {"selections": [{}] * (graph_api.MAX_SELECTED_RESOURCES + 1)},
            {
                "selections": [
                    {
                        "resource_id": str(uuid.uuid4()),
                        "row_ids": [""] * (graph_api.MAX_ROWS_PER_SELECTION + 1),
                    }
                ]
            },
        ):
            with self.subTest(body=body), self.assertRaises(ValueError):
                graph_api._parse_selections(body)

    def test_path_ids_are_validated_and_bounded(self):
        self.assertEqual(graph_api._parse_path_relationship_ids({}), [])
        for values in (
            "bad",
            ["bad"],
            [str(uuid.uuid4())] * (graph_api.MAX_PATH_RELATIONSHIPS + 1),
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                graph_api._parse_path_relationship_ids(
                    {"path_relationship_ids": values}
                )


@override_settings(
    PERMISSION_FRAMEWORK="arches_default_deny.ArchesDefaultDenyPermissionFramework"
)
class RelationshipGraphTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(username="graph-admin")
        cls.member = User.objects.create_user(username="graph-member")
        cls.outsider = User.objects.create_user(username="graph-outsider")
        cls.group = Group.objects.create(name="graph-readers")
        cls.member.groups.add(cls.group)
        lifecycle = ResourceInstanceLifecycle.objects.create(name="Test lifecycle")
        cls.editable_state = ResourceInstanceLifecycleState.objects.create(
            name="Editable",
            action_label="Edit",
            can_edit_resource_instances=True,
            resource_instance_lifecycle=lifecycle,
        )
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Graph",
            slug="relationship-test",
            isresource=True,
            resource_instance_lifecycle=lifecycle,
        )
        cls.other_graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            name="Other",
            slug="relationship-other",
            isresource=True,
            resource_instance_lifecycle=lifecycle,
        )
        cls.seed, cls.related, cls.denied, cls.owned, cls.target = [
            ResourceInstance(
                resourceinstanceid=uuid.uuid4(),
                graph=cls.graph,
                resource_instance_lifecycle_state=cls.editable_state,
            )
            for _ in range(5)
        ]
        cls.owned.principaluser = cls.member
        cls.other = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.other_graph,
            resource_instance_lifecycle_state=cls.editable_state,
        )
        ResourceInstance.objects.bulk_create(
            [cls.seed, cls.related, cls.denied, cls.owned, cls.target, cls.other]
        )
        for resource in (cls.seed, cls.related, cls.target, cls.other):
            assign_perm("view_resourceinstance", cls.group, resource)

        # Core's read check needs one readable nodegroup per model.
        visible_nodes = []
        for graph in (cls.graph, cls.other_graph):
            visible_nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
            visible_nodes.append(
                Node(
                    nodeid=visible_nodegroup.pk,
                    graph=graph,
                    nodegroup=visible_nodegroup,
                    name="Visible",
                    alias="visible",
                    datatype="string",
                    istopnode=False,
                )
            )
        Node.objects.bulk_create(visible_nodes)

        cls.nodegroup = NodeGroup.objects.create(nodegroupid=uuid.uuid4())
        cls.hidden_node = Node(
            nodeid=cls.nodegroup.pk,
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            name="Hidden relationship",
            alias="hidden_relationship",
            datatype="resource-instance",
            istopnode=False,
        )
        Node.objects.bulk_create([cls.hidden_node])
        assign_perm("write_nodegroup", cls.member, cls.nodegroup)
        cls.forward = cls.make_relation(cls.seed, cls.related, "forward", "")
        cls.inverse = cls.make_relation(cls.related, cls.seed, "forward", "inverse")
        cls.fallback = cls.make_relation(cls.related, cls.seed, "forward", None)
        cls.blank = cls.make_relation(cls.related, cls.seed, None, "")
        cls.empty = cls.make_relation(cls.related, cls.seed, "", None)
        cls.self_link = cls.make_relation(cls.seed, cls.seed, None, None)
        cls.hidden = cls.make_relation(
            cls.seed, cls.related, "hidden", node=cls.hidden_node
        )
        cls.restricted_out = cls.make_relation(cls.seed, cls.denied, "restricted")
        cls.restricted_in = cls.make_relation(cls.denied, cls.seed, "restricted")
        cls.owned_link = cls.make_relation(cls.seed, cls.owned, "owned")
        cls.other_link = cls.make_relation(cls.seed, cls.other, "forward")
        cls.second_hop = cls.make_relation(cls.related, cls.target, "next")

    @classmethod
    def make_relation(cls, source, target, type_id="", inverse="", node=None):
        return ResourceXResource.objects.create(
            resourcexid=uuid.uuid4(),
            from_resource=source,
            to_resource=target,
            from_resource_graph=source.graph,
            to_resource_graph=target.graph,
            relationshiptype=type_id,
            inverserelationshiptype=inverse,
            node=node,
        )

    def selected(self, user, resource=None):
        resource = resource or self.seed
        readable = ReadableNodes(user)
        counts = graph_api._count_relationships(user, readable, resource.pk)
        return counts, graph_api._selected_relations(
            user, readable, [(resource.pk, list(counts))]
        )

    def graph_response(self, user=None, selections=None, path_ids=None):
        if selections is None:
            counts, _relations = self.selected(user or self.member)
            selections = [
                {
                    "resource_id": str(self.seed.pk),
                    "row_ids": [
                        f"{direction}|{type_id}|{graph_id}"
                        for direction, type_id, graph_id in counts
                    ],
                }
            ]
        request = RequestFactory().post(
            "/graph",
            data=json.dumps(
                {"selections": selections, "path_relationship_ids": path_ids or []}
            ),
            content_type="application/json",
        )
        request.user = user or self.member
        return graph_api.RelationshipGraphAPI().post(request)

    def test_selected_rows_match_every_summary_group(self):
        for user in (self.admin, self.member, self.outsider):
            for resource in (self.seed, self.related):
                readable = ReadableNodes(user)
                counts = graph_api._count_relationships(user, readable, resource.pk)
                for row, count in counts.items():
                    with self.subTest(
                        user=user.username, row=row, resource=resource.pk
                    ):
                        selected = graph_api._selected_relations(
                            user, readable, [(resource.pk, [row])]
                        )
                        self.assertEqual(len(selected), count)

    def test_permissions_exclude_both_directions_and_unreadable_nodes(self):
        _counts, selected = self.selected(self.member)
        self.assertEqual(
            set(selected),
            {
                relation.pk
                for relation in (
                    self.forward,
                    self.inverse,
                    self.fallback,
                    self.blank,
                    self.empty,
                    self.self_link,
                    self.owned_link,
                    self.other_link,
                )
            },
        )

    def test_incoming_fallback_blank_and_model_filters(self):
        expected = (
            (("incoming", "inverse", self.graph.pk), {self.inverse.pk}),
            (("incoming", "forward", self.graph.pk), {self.fallback.pk}),
            (("incoming", "", self.graph.pk), {self.blank.pk, self.empty.pk}),
            (("outgoing", "", self.graph.pk), {self.self_link.pk}),
            (("outgoing", "forward", self.other_graph.pk), {self.other_link.pk}),
        )
        for row, ids in expected:
            with self.subTest(row=row):
                self.assertEqual(
                    set(
                        graph_api._selected_relations(
                            self.member,
                            ReadableNodes(self.member),
                            [(self.seed.pk, [row])],
                        )
                    ),
                    ids,
                )

    def test_selections_are_one_query_and_deduplicate_shared_edges(self):
        selections = [
            (self.seed.pk, [("outgoing", "forward", self.graph.pk)]),
            (self.related.pk, [("incoming", "forward", self.graph.pk)]),
        ]
        with self.assertNumQueries(1):
            selected = graph_api._selected_relations(
                self.admin, ReadableNodes(None), selections
            )
        self.assertEqual(set(selected), {self.forward.pk})

    def test_empty_selection_makes_no_relationship_query(self):
        with self.assertNumQueries(0):
            self.assertEqual(
                graph_api._selected_relations(
                    self.member, ReadableNodes(None), [(self.seed.pk, [])]
                ),
                {},
            )

    def test_selection_limit_is_in_sql_not_python(self):
        now = timezone.now()
        ResourceXResource.objects.bulk_create(
            [
                ResourceXResource(
                    resourcexid=uuid.uuid4(),
                    from_resource=self.seed,
                    to_resource=self.related,
                    from_resource_graph=self.graph,
                    to_resource_graph=self.graph,
                    relationshiptype="parallel",
                    created=now,
                    modified=now,
                )
                for _ in range(20)
            ]
        )
        with (
            patch.object(graph_api, "MAX_GRAPH_EDGES", 3),
            CaptureQueriesContext(connection) as queries,
        ):
            selected = graph_api._selected_relations(
                self.admin,
                ReadableNodes(None),
                [(self.seed.pk, [("outgoing", "parallel", self.graph.pk)])],
            )
        self.assertEqual(len(selected), 4)
        self.assertEqual(len(queries), 1)
        self.assertIn("LIMIT 4", queries[0]["sql"])

    def test_supplied_path_checks_both_ends_and_node_permissions(self):
        readable = ReadableNodes(self.member)
        selected = graph_api._readable_relations_by_id(
            self.member,
            readable,
            [
                self.forward.pk,
                self.hidden.pk,
                self.restricted_in.pk,
                self.restricted_out.pk,
            ],
        )
        self.assertEqual(set(selected), {self.forward.pk})
        for relation in (self.hidden, self.restricted_in, self.restricted_out):
            with self.subTest(relation=relation.pk):
                self.assertEqual(
                    self.graph_response(path_ids=[str(relation.pk)]).status_code, 404
                )

    def test_unreadable_seed_is_indistinguishable_from_missing(self):
        for resource_id in (self.denied.pk, uuid.uuid4()):
            response = self.graph_response(
                selections=[{"resource_id": str(resource_id), "row_ids": []}]
            )
            self.assertEqual(response.status_code, 404)

    def test_graph_caps_edges_and_reserves_path(self):
        with patch.object(graph_api, "MAX_GRAPH_EDGES", 2):
            response = self.graph_response(path_ids=[str(self.second_hop.pk)])
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["truncated"])
        self.assertEqual(len(data["edges"]), 2)
        self.assertEqual(data["edge_limit"], 2)
        self.assertIn(str(self.second_hop.pk), [edge["id"] for edge in data["edges"]])
        self.assertTrue(
            next(
                edge for edge in data["edges"] if edge["id"] == str(self.second_hop.pk)
            )["on_path"]
        )

    def test_graph_caps_nodes_and_has_no_dangling_edges(self):
        with patch.object(graph_api, "MAX_GRAPH_NODES", 2):
            data = json.loads(self.graph_response().content)
        self.assertTrue(data["truncated"])
        self.assertLessEqual(len(data["nodes"]), 2)
        node_ids = {node["id"] for node in data["nodes"]}
        for edge in data["edges"]:
            self.assertTrue({edge["source"], edge["target"]} <= node_ids)

    def test_exact_limit_is_not_truncated(self):
        selections = [
            {
                "resource_id": str(self.seed.pk),
                "row_ids": [f"outgoing|forward|{self.graph.pk}"],
            }
        ]
        with patch.object(graph_api, "MAX_GRAPH_EDGES", 1):
            data = json.loads(self.graph_response(selections=selections).content)
        self.assertFalse(data["truncated"])
        self.assertEqual(len(data["edges"]), 1)

    def test_related_counts_are_exact_and_count_self_once(self):
        readable = ReadableNodes(self.member)
        counts = graph_api._count_relationships(self.member, readable, self.seed.pk)
        related_counts = graph_api._related_counts(
            self.member, readable, [self.seed.pk]
        )
        self.assertEqual(related_counts[self.seed.pk], sum(counts.values()))
        self.assertEqual(related_counts[self.seed.pk], 8)

    def paths(self, source, target):
        return graph_api._shortest_path(
            self.member, ReadableNodes(self.member), source.pk, target.pk
        )

    def test_every_shortest_path_in_both_directions(self):
        # The five readable relationships between seed and related are five
        # equally short ways from one to the other
        parallel = {
            relation.pk
            for relation in (
                self.forward,
                self.inverse,
                self.fallback,
                self.blank,
                self.empty,
            )
        }
        for source, target, hops, ids in (
            (self.seed, self.target, 2, parallel | {self.second_hop.pk}),
            (self.target, self.seed, 2, parallel | {self.second_hop.pk}),
            (self.seed, self.related, 1, parallel),
        ):
            with self.subTest(source=source.pk, target=target.pk):
                paths = self.paths(source, target)
                self.assertEqual(set(paths.relationship_ids), ids)
                self.assertEqual(paths.hops, hops)
                self.assertEqual(paths.path_count, 5)
                self.assertFalse(paths.truncated)
                self.assertFalse(paths.limit_reached)

    def test_paths_through_different_resources_are_all_found(self):
        # A second way from seed to target, through other, is as short as the
        # ones through related, and a longer one through owned is not kept
        to_target = self.make_relation(self.other, self.target, "next")
        longer = self.make_relation(self.owned, self.other, "detour")
        paths = self.paths(self.seed, self.target)
        self.assertEqual(paths.hops, 2)
        self.assertEqual(paths.path_count, 5 + 1)
        self.assertIn(self.other_link.pk, paths.relationship_ids)
        self.assertIn(to_target.pk, paths.relationship_ids)
        self.assertIn(self.second_hop.pk, paths.relationship_ids)
        self.assertNotIn(longer.pk, paths.relationship_ids)
        self.assertNotIn(self.owned_link.pk, paths.relationship_ids)

    def test_too_many_paths_keep_whole_paths(self):
        with patch.object(graph_api, "MAX_PATH_RELATIONSHIPS", 3):
            paths = self.paths(self.seed, self.target)
        self.assertTrue(paths.truncated)
        self.assertEqual(paths.path_count, 5)
        # One whole chain is kept: one of the parallel links, then the next hop
        self.assertEqual(len(paths.relationship_ids), 2)
        self.assertIn(self.second_hop.pk, paths.relationship_ids)

    def test_hidden_and_denied_bridges_do_not_provide_a_path(self):
        isolated = ResourceInstance(
            resourceinstanceid=uuid.uuid4(),
            graph=self.graph,
            resource_instance_lifecycle_state=self.editable_state,
        )
        ResourceInstance.objects.bulk_create([isolated])
        assign_perm("view_resourceinstance", self.group, isolated)
        self.make_relation(self.denied, isolated)
        self.make_relation(self.related, isolated, node=self.hidden_node)
        paths = self.paths(self.seed, isolated)
        self.assertEqual(paths, graph_api.NO_PATHS)

    def test_hub_expansion_is_sql_bounded_and_reports_incomplete(self):
        with (
            patch.object(graph_api, "MAX_PATH_SEARCH_NODES", 3),
            CaptureQueriesContext(connection) as queries,
        ):
            paths = graph_api._shortest_path(
                self.admin, ReadableNodes(None), self.seed.pk, self.target.pk
            )
        self.assertEqual(paths, replace(graph_api.NO_PATHS, limit_reached=True))
        self.assertEqual(len(queries), 1)
        self.assertIn("LIMIT 2", queries[0]["sql"])

    def test_path_hop_limit_is_not_a_size_limit(self):
        with patch.object(graph_api, "MAX_PATH_HOPS", 1):
            paths = self.paths(self.seed, self.target)
        self.assertEqual(paths, graph_api.NO_PATHS)

    def test_direct_relationships_are_bounded_and_marked(self):
        with (
            patch.object(graph_api, "MAX_GRAPH_EDGES", 1),
            CaptureQueriesContext(connection) as queries,
        ):
            direct, limited = graph_api._direct_relationships(
                ReadableNodes(None), self.seed.pk, self.related.pk
            )
        self.assertEqual(len(direct), 1)
        self.assertTrue(limited)
        self.assertIn("LIMIT 2", queries[0]["sql"])

    def test_descriptor_edit_permission_is_separate_from_read_permission(self):
        ids = [str(self.seed.pk), str(self.denied.pk)]
        batch_request = RequestFactory().get("/descriptors", {"ids": ids})
        batch_request.user = self.member
        data = json.loads(ResourceDescriptorsAPI().get(batch_request).content)
        self.assertNotIn("can_edit", data[str(self.seed.pk)])

        request = RequestFactory().get(
            "/descriptors", {"ids": ids, "include_can_edit": "true"}
        )
        request.user = self.member
        data = json.loads(ResourceDescriptorsAPI().get(request).content)
        self.assertFalse(data[str(self.seed.pk)]["can_edit"])
        self.assertNotIn(str(self.denied.pk), data)
        assign_perm("change_resourceinstance", self.member, self.seed)
        data = json.loads(ResourceDescriptorsAPI().get(request).content)
        self.assertTrue(data[str(self.seed.pk)]["can_edit"])

    def related_resources(self, row_id, user=None, resource=None, **params):
        request = RequestFactory().get(
            "/related-resources",
            {
                "resource_id": str((resource or self.seed).pk),
                "row_id": row_id,
                **params,
            },
        )
        request.user = user or self.member
        return graph_api.RelationshipGraphRelatedResourcesAPI().get(request)

    def test_related_resources_add_up_to_every_summary_row(self):
        for user in (self.admin, self.member, self.outsider):
            counts = graph_api._count_relationships(
                user, ReadableNodes(user), self.seed.pk
            )
            for (direction, type_id, graph_id), count in counts.items():
                row_id = f"{direction}|{type_id}|{graph_id}"
                with self.subTest(user=user.username, row=row_id):
                    response = self.related_resources(row_id, user=user)
                    self.assertEqual(response.status_code, 200)
                    data = json.loads(response.content)
                    self.assertEqual(len(data["resources"]), count)
                    self.assertIsNone(data["next_offset"])

    def test_related_resources_list_the_far_end_of_each_relationship(self):
        expected = (
            (f"outgoing|forward|{self.graph.pk}", self.forward, self.related),
            (f"incoming|inverse|{self.graph.pk}", self.inverse, self.related),
            (f"incoming|forward|{self.graph.pk}", self.fallback, self.related),
            (f"outgoing||{self.graph.pk}", self.self_link, self.seed),
        )
        for row_id, relation, resource in expected:
            with self.subTest(row=row_id):
                data = json.loads(self.related_resources(row_id).content)
                self.assertEqual(
                    data["resources"],
                    [
                        {
                            "relationship_id": str(relation.pk),
                            "resource_id": str(resource.pk),
                            "name": str(resource.pk),
                        }
                    ],
                )

    def test_related_resources_exclude_unreadable_ends_and_nodes(self):
        for row_id in (
            f"outgoing|restricted|{self.graph.pk}",
            f"incoming|restricted|{self.graph.pk}",
            f"outgoing|hidden|{self.graph.pk}",
        ):
            with self.subTest(row=row_id):
                data = json.loads(self.related_resources(row_id).content)
                self.assertEqual(data["resources"], [])
        admin = json.loads(
            self.related_resources(
                f"outgoing|restricted|{self.graph.pk}", user=self.admin
            ).content
        )
        self.assertEqual(len(admin["resources"]), 1)

    def test_related_resources_page_by_name(self):
        now = timezone.now()
        names = ["delta", "Alpha", "charlie", "Bravo", "echo"]
        resources = [
            ResourceInstance(
                resourceinstanceid=uuid.uuid4(),
                graph=self.other_graph,
                resource_instance_lifecycle_state=self.editable_state,
                descriptors={"en": {"name": name}},
            )
            for name in names
        ]
        ResourceInstance.objects.bulk_create(resources)
        # "Alpha" is related twice, so it is listed twice
        resources.insert(0, resources[1])
        ResourceXResource.objects.bulk_create(
            [
                ResourceXResource(
                    resourcexid=uuid.uuid4(),
                    from_resource=self.seed,
                    to_resource=resource,
                    from_resource_graph=self.graph,
                    to_resource_graph=self.other_graph,
                    relationshiptype="listed",
                    created=now,
                    modified=now,
                )
                for resource in resources
            ]
        )
        row_id = f"outgoing|listed|{self.other_graph.pk}"
        seen = []
        relationship_ids = []
        offset = 0
        with override_settings(LANGUAGE_CODE="en"):
            while offset is not None:
                data = json.loads(
                    self.related_resources(
                        row_id, user=self.admin, offset=offset, limit=2
                    ).content
                )
                seen += [resource["name"] for resource in data["resources"]]
                relationship_ids += [
                    resource["relationship_id"] for resource in data["resources"]
                ]
                offset = data["next_offset"]
        self.assertEqual(seen, ["Alpha", "Alpha", "Bravo", "charlie", "delta", "echo"])
        self.assertEqual(len(set(relationship_ids)), 6)

        with override_settings(LANGUAGE_CODE="en"):
            for term, expected in (
                ("ALPHA", ["Alpha", "Alpha"]),
                (" ar ", ["charlie"]),
                ("zulu", []),
                ("", ["Alpha", "Alpha", "Bravo", "charlie", "delta", "echo"]),
            ):
                with self.subTest(term=term):
                    data = json.loads(
                        self.related_resources(
                            row_id, user=self.admin, term=term
                        ).content
                    )
                    self.assertEqual(
                        [resource["name"] for resource in data["resources"]],
                        expected,
                    )

    def test_related_resources_reject_bad_input_and_hide_unreadable_seed(self):
        row_id = f"outgoing|forward|{self.graph.pk}"
        for params in (
            {"row_id": "bad"},
            {"offset": -1},
            {"offset": "x"},
            {"limit": 0},
            {"limit": graph_api.MAX_RELATED_RESOURCES_PAGE + 1},
            {"term": "x" * (graph_api.MAX_RELATED_RESOURCES_TERM_LENGTH + 1)},
        ):
            with self.subTest(params=params):
                params = {"row_id": row_id, **params}
                self.assertEqual(
                    self.related_resources(params.pop("row_id"), **params).status_code,
                    400,
                )
        self.assertEqual(
            self.related_resources(row_id, resource=self.denied).status_code, 404
        )
