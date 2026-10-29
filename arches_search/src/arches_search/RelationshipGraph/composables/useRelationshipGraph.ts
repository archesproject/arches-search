import { computed, onScopeDispose, ref, shallowRef, toValue, watch } from "vue";

import { fetchRelationshipGraph } from "@/arches_search/RelationshipGraph/api.ts";

import type { MaybeRefOrGetter } from "vue";
import type {
    RelationshipGraphData,
    RowSelection,
} from "@/arches_search/RelationshipGraph/types.ts";

const IDLE = "idle" as const;
const LOADING = "loading" as const;
const LOADED = "loaded" as const;
const FAILED = "failed" as const;

type GraphStatus = typeof IDLE | typeof LOADING | typeof LOADED | typeof FAILED;

// Rows may be toggled in quick succession, so a change waits for a pause
const SELECTION_DEBOUNCE_MS = 250;

// Loads the graph for the selected rows, but only while it is wanted. The
// first load is immediate; after that it follows the selection, so toggling
// a row in the graph view brings its resources in or takes them out.
export function useRelationshipGraph(
    selections: MaybeRefOrGetter<RowSelection[]>,
    isActive: MaybeRefOrGetter<boolean>,
) {
    // Replaced whole, never edited, so there is no use making it deeply reactive
    const graphData = shallowRef<RelationshipGraphData | null>(null);
    const status = ref<GraphStatus>(IDLE);

    const isLoading = computed<boolean>(() => status.value === LOADING);
    const hasFailed = computed<boolean>(() => status.value === FAILED);

    let loadedSelectionKey: string | null = null;
    let latestRequestId = 0;
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    watch(
        [() => JSON.stringify(toValue(selections)), () => toValue(isActive)],
        ([selectionKey, active]) => {
            clearDebounceTimer();
            if (!active) return;
            if (selectionKey === loadedSelectionKey) return;

            // Nothing selected means nothing to show, and no answer still on
            // its way is of any use
            if (toValue(selections).length === 0) {
                clearGraph();
                return;
            }

            const delay = graphData.value ? SELECTION_DEBOUNCE_MS : 0;
            debounceTimer = setTimeout(() => {
                debounceTimer = null;
                void loadGraph();
            }, delay);
        },
        { immediate: true },
    );

    onScopeDispose(clearDebounceTimer);

    function clearDebounceTimer(): void {
        if (debounceTimer !== null) {
            clearTimeout(debounceTimer);
            debounceTimer = null;
        }
    }

    function clearGraph(): void {
        latestRequestId++;
        loadedSelectionKey = null;
        graphData.value = null;
        status.value = IDLE;
    }

    async function loadGraph(): Promise<void> {
        const requestedSelections = toValue(selections);
        if (requestedSelections.length === 0) return;

        const requestId = ++latestRequestId;
        loadedSelectionKey = JSON.stringify(requestedSelections);
        status.value = LOADING;
        try {
            const loadedGraph =
                await fetchRelationshipGraph(requestedSelections);
            if (requestId !== latestRequestId) return;
            graphData.value = loadedGraph;
            status.value = LOADED;
        } catch {
            if (requestId !== latestRequestId) return;
            // Forget it, so that the same selection can be tried again
            loadedSelectionKey = null;
            status.value = FAILED;
        }
    }

    return { graphData, isLoading, hasFailed, loadGraph };
}
