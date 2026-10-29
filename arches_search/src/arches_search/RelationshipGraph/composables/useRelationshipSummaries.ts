import { computed, ref, toValue, watch } from "vue";

import { fetchRelationshipSummary } from "@/arches_search/RelationshipGraph/api.ts";
import {
    FAILED,
    LOADED,
    LOADING,
} from "@/arches_search/RelationshipGraph/utils/load-status.ts";

import type { MaybeRefOrGetter } from "vue";
import type {
    RelationshipSummary,
    RowSelection,
} from "@/arches_search/RelationshipGraph/types.ts";

export type SummaryState =
    | { status: typeof LOADING }
    | { status: typeof FAILED }
    | { status: typeof LOADED; summary: RelationshipSummary };

// Loads the summary of each resource, and tracks which of its rows the user
// has switched off. Every row is on until deselected, so a row that appears
// later (a newly added resource) starts on without any bookkeeping.
export function useRelationshipSummaries(
    resourceIds: MaybeRefOrGetter<string[]>,
) {
    const summaryStates = ref<Record<string, SummaryState>>({});
    const deselectedRowIds = ref<Record<string, string[]>>({});

    const selectedRelationshipCount = computed<number>(() => {
        let total = 0;
        for (const [resourceId, state] of Object.entries(summaryStates.value)) {
            if (state.status !== LOADED) continue;
            for (const row of state.summary.rows) {
                if (isRowSelected(resourceId, row.id)) total += row.count;
            }
        }
        return total;
    });

    // What the graph should draw: each loaded resource, with its selected rows
    const selections = computed<RowSelection[]>(() =>
        toValue(resourceIds).flatMap((resourceId) => {
            const state = summaryStates.value[resourceId];
            if (state?.status !== LOADED) return [];
            return [
                {
                    resource_id: resourceId,
                    row_ids: state.summary.rows
                        .filter((row) => isRowSelected(resourceId, row.id))
                        .map((row) => row.id),
                },
            ];
        }),
    );

    const isLoading = computed<boolean>(() =>
        Object.values(summaryStates.value).some(
            (state) => state.status === LOADING,
        ),
    );

    // The request each resource is waiting on, so that an answer to an earlier
    // one (a retry, or a resource removed and added again) is thrown away
    const latestRequestIds: Record<string, number> = {};
    let requestCount = 0;

    // Not a watchEffect: it would also track summaryStates, which it writes
    watch(
        () => toValue(resourceIds),
        (currentIds) => {
            for (const resourceId of Object.keys(summaryStates.value)) {
                if (!currentIds.includes(resourceId)) {
                    delete summaryStates.value[resourceId];
                    delete deselectedRowIds.value[resourceId];
                    // A resource that was removed has no request to wait for
                    delete latestRequestIds[resourceId];
                }
            }
            for (const resourceId of currentIds) {
                if (!summaryStates.value[resourceId]) {
                    void loadSummary(resourceId);
                }
            }
        },
        { immediate: true },
    );

    async function loadSummary(resourceId: string): Promise<void> {
        const requestId = ++requestCount;
        latestRequestIds[resourceId] = requestId;
        summaryStates.value[resourceId] = { status: LOADING };
        let nextState: SummaryState;
        try {
            nextState = {
                status: LOADED,
                summary: await fetchRelationshipSummary(resourceId),
            };
        } catch {
            nextState = { status: FAILED };
        }
        if (latestRequestIds[resourceId] === requestId) {
            summaryStates.value[resourceId] = nextState;
        }
    }

    function isRowSelected(resourceId: string, rowId: string): boolean {
        return !deselectedRowIds.value[resourceId]?.includes(rowId);
    }

    function toggleRow(resourceId: string, rowId: string): void {
        const deselected = deselectedRowIds.value[resourceId] ?? [];
        deselectedRowIds.value[resourceId] = deselected.includes(rowId)
            ? deselected.filter((deselectedId) => deselectedId !== rowId)
            : [...deselected, rowId];
    }

    return {
        summaryStates,
        deselectedRowIds,
        selectedRelationshipCount,
        selections,
        isLoading,
        isRowSelected,
        toggleRow,
        loadSummary,
    };
}
