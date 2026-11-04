import { computed, ref, toValue, watch } from "vue";

import { fetchRelatedResources } from "@/arches_search/RelationshipGraph/api.ts";
import {
    FAILED,
    LOADED,
    LOADING,
} from "@/arches_search/RelationshipGraph/utils/load-status.ts";

import type { MaybeRefOrGetter } from "vue";
import type { RelatedResource } from "@/arches_search/RelationshipGraph/types.ts";

export const RELATED_RESOURCES_PAGE_SIZE = 50;

// The resources behind one summary row, fetched a page at a time as the list
// is scrolled, and narrowed to those whose name contains the term. Pages are
// only ever appended, so a page that fails can be retried without losing the
// ones already shown; a new term starts again from the first page.
export function useRelatedResources(
    resourceId: string,
    rowId: string,
    term: MaybeRefOrGetter<string> = "",
) {
    const resources = ref<RelatedResource[]>([]);
    const status = ref<
        typeof LOADING | typeof LOADED | typeof FAILED | undefined
    >();
    const nextOffset = ref<number | null>(0);

    const hasMore = computed<boolean>(() => nextOffset.value !== null);
    const isLoading = computed<boolean>(() => status.value === LOADING);
    const hasFailed = computed<boolean>(() => status.value === FAILED);
    const currentTerm = computed<string>(() => toValue(term).trim());

    // The request the list is waiting on, so that a page asked for under an
    // earlier term is thrown away when it arrives
    let requestCount = 0;

    async function loadMore(): Promise<void> {
        const offset = nextOffset.value;
        // One page at a time; a failed page waits for an explicit retry
        if (offset === null || status.value === LOADING) return;
        const requestId = ++requestCount;
        status.value = LOADING;
        try {
            const page = await fetchRelatedResources(
                resourceId,
                rowId,
                offset,
                RELATED_RESOURCES_PAGE_SIZE,
                currentTerm.value,
            );
            if (requestId !== requestCount) return;
            resources.value.push(...page.resources);
            nextOffset.value = page.next_offset;
            status.value = LOADED;
        } catch {
            if (requestId !== requestCount) return;
            status.value = FAILED;
        }
    }

    watch(currentTerm, () => {
        requestCount++;
        resources.value = [];
        nextOffset.value = 0;
        status.value = undefined;
        void loadMore();
    });

    return {
        resources,
        hasMore,
        isLoading,
        hasFailed,
        currentTerm,
        loadMore,
    };
}
