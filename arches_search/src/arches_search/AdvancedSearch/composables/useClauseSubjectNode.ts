import { computed, inject, ref, watch } from "vue";

import { ClauseSubjectTypeToken } from "@/arches_search/AdvancedSearch/types.ts";

import type { ComputedRef, Ref } from "vue";
import type {
    ClauseSubject,
    GraphModel,
    Node,
} from "@/arches_search/AdvancedSearch/types.ts";

export function useClauseSubjectNode(
    subject: Readonly<Ref<ClauseSubject | undefined>>,
): {
    subjectGraph: ComputedRef<GraphModel | null>;
    subjectNode: ComputedRef<Node | null>;
} {
    const graphs = inject<Ref<GraphModel[]>>("graphs")!;
    const getNodesForGraphId =
        inject<(graphId: string) => Promise<Node[]>>("getNodesForGraphId")!;

    const nodesByGraphId = ref<Record<string, Node[]>>({});

    const subjectGraph = computed<GraphModel | null>(
        () =>
            graphs.value.find(
                (graph) => graph.slug === subject.value?.graph_slug,
            ) ?? null,
    );

    const subjectNode = computed<Node | null>(() => {
        if (
            !subjectGraph.value ||
            subject.value?.type !== ClauseSubjectTypeToken.NODE
        ) {
            return null;
        }
        const nodeAlias = subject.value.node_alias;
        const nodes = nodesByGraphId.value[subjectGraph.value.graphid] ?? [];
        return (
            nodes.find(
                (node) => node.alias === nodeAlias && node.selectable !== false,
            ) ?? null
        );
    });

    watch(
        subjectGraph,
        (graph) => {
            if (graph) {
                void loadNodes(graph.graphid);
            }
        },
        { immediate: true },
    );

    async function loadNodes(graphId: string): Promise<void> {
        try {
            const nodes = await getNodesForGraphId(graphId);
            nodesByGraphId.value = {
                ...nodesByGraphId.value,
                [graphId]: nodes,
            };
        } catch (error) {
            console.error(error);
        }
    }

    return { subjectGraph, subjectNode };
}
