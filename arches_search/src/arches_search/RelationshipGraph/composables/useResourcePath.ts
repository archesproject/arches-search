import { computed, ref, toValue, watch } from "vue";

import { fetchRelationshipPath } from "@/arches_search/RelationshipGraph/api.ts";
import {
    FAILED,
    LOADED,
    LOADING,
} from "@/arches_search/RelationshipGraph/utils/load-status.ts";

import type { MaybeRefOrGetter } from "vue";
import type { RelationshipPath } from "@/arches_search/RelationshipGraph/types.ts";

export type PathState =
    | { status: typeof LOADING }
    | { status: typeof FAILED }
    | { status: typeof LOADED; path: RelationshipPath };

// How the two resources being compared are related. There is nothing to ask
// unless exactly two are selected, and the answer belongs to that pair, so a
// different pair starts over, with the path hidden again.
export function useResourcePath(resourceIds: MaybeRefOrGetter<string[]>) {
    const pathState = ref<PathState | null>(null);
    const isPathShown = ref(false);

    let latestRequestId = 0;

    // The relationships the graph should draw as the path, while it is wanted
    const shownPathRelationshipIds = computed<string[]>(() =>
        isPathShown.value && pathState.value?.status === LOADED
            ? pathState.value.path.relationship_ids
            : [],
    );

    watch(
        () => {
            const ids = toValue(resourceIds);
            return ids.length === 2 ? `${ids[0]}|${ids[1]}` : null;
        },
        (pairKey) => {
            isPathShown.value = false;
            if (pairKey === null) {
                // Anything still on its way no longer matters
                latestRequestId++;
                pathState.value = null;
                return;
            }
            void loadPath();
        },
        { immediate: true },
    );

    async function loadPath(): Promise<void> {
        const [fromId, toId] = toValue(resourceIds);
        if (toValue(resourceIds).length !== 2) return;

        const requestId = ++latestRequestId;
        pathState.value = { status: LOADING };
        let nextState: PathState;
        try {
            nextState = {
                status: LOADED,
                path: await fetchRelationshipPath(fromId, toId),
            };
        } catch {
            nextState = { status: FAILED };
        }
        if (requestId === latestRequestId) {
            pathState.value = nextState;
        }
    }

    function togglePath(): void {
        isPathShown.value = !isPathShown.value;
    }

    return {
        pathState,
        isPathShown,
        shownPathRelationshipIds,
        togglePath,
        loadPath,
    };
}
