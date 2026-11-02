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
    subjectNode: Ref<Node | null>;
} {
    const graphs = inject<Ref<GraphModel[]>>("graphs")!;
    const getNodesForGraphId =
        inject<(graphId: string) => Promise<Node[]>>("getNodesForGraphId")!;

    const subjectNode = ref<Node | null>(null);

    const subjectGraph = computed<GraphModel | null>(
        () =>
            graphs.value.find(
                (graph) => graph.slug === subject.value?.graph_slug,
            ) ?? null,
    );

    watch(
        [
            subjectGraph,
            () => subject.value?.type,
            () => subject.value?.node_alias,
        ],
        async (
            [graph, subjectType, nodeAlias],
            _previousSources,
            onCleanup,
        ) => {
            let isStale = false;
            onCleanup(() => {
                isStale = true;
            });

            subjectNode.value = null;
            if (
                !graph ||
                subjectType !== ClauseSubjectTypeToken.NODE ||
                !nodeAlias
            ) {
                return;
            }

            try {
                const nodes = await getNodesForGraphId(graph.graphid);
                if (isStale) {
                    return;
                }
                subjectNode.value =
                    nodes.find(
                        (node) =>
                            node.alias === nodeAlias &&
                            node.selectable !== false,
                    ) ?? null;
            } catch (error) {
                console.error(error);
            }
        },
        { immediate: true },
    );

    return { subjectGraph, subjectNode };
}
