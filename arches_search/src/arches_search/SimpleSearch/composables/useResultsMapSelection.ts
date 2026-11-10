import { inject, provide, ref, shallowRef } from "vue";

import type { InjectionKey, Ref, ShallowRef } from "vue";

export interface ResultsMapFocusRequest {
    resourceId: string;
}

export interface ResultsMapSelection {
    hoveredResourceId: Ref<string | null>;
    selectedResourceId: Ref<string | null>;
    pinnedResourceId: Ref<string | null>;
    focusRequest: ShallowRef<ResultsMapFocusRequest | null>;
    showOnMap: (resourceId: string) => void;
    unpin: () => void;
}

const RESULTS_MAP_SELECTION_KEY: InjectionKey<ResultsMapSelection> = Symbol(
    "resultsMapSelection",
);

export function provideResultsMapSelection({
    openMap,
}: {
    openMap: () => void;
}): ResultsMapSelection {
    const hoveredResourceId = ref<string | null>(null);
    const selectedResourceId = ref<string | null>(null);
    const pinnedResourceId = ref<string | null>(null);
    const focusRequest = shallowRef<ResultsMapFocusRequest | null>(null);

    function showOnMap(resourceId: string): void {
        selectedResourceId.value = resourceId;
        focusRequest.value = { resourceId };
        openMap();
    }

    function unpin(): void {
        if (selectedResourceId.value === pinnedResourceId.value) {
            selectedResourceId.value = null;
        }
        pinnedResourceId.value = null;
    }

    const resultsMapSelection: ResultsMapSelection = {
        hoveredResourceId,
        selectedResourceId,
        pinnedResourceId,
        focusRequest,
        showOnMap,
        unpin,
    };
    provide(RESULTS_MAP_SELECTION_KEY, resultsMapSelection);
    return resultsMapSelection;
}

export function useResultsMapSelection(): ResultsMapSelection | null {
    return inject(RESULTS_MAP_SELECTION_KEY, null);
}
