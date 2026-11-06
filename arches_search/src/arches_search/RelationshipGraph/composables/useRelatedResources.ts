import { computed, onScopeDispose, ref, watch } from "vue";

import { fetchRelatedResources } from "@/arches_search/RelationshipGraph/api.ts";

import type { RelatedResource } from "@/arches_search/RelationshipGraph/types.ts";

export const RELATED_RESOURCES_PAGE_SIZE = 50;
const FILTER_DEBOUNCE_MS = 300;

// The resources behind one summary row, fetched a page at a time as the list
// is scrolled, and narrowed to those whose name contains the filter text once
// typing pauses. Pages are only ever appended, so a page that fails waits for
// retry() without losing the ones already shown; a new term starts again from
// the first page.
export function useRelatedResources(resourceId: string, rowId: string) {
    const filterText = ref("");
    const currentTerm = ref("");
    const resources = ref<RelatedResource[]>([]);
    const nextOffset = ref<number | null>(0);
    const isLoading = ref(false);
    const hasFailed = ref(false);

    const hasMore = computed<boolean>(() => nextOffset.value !== null);

    // The request the list is waiting on, so that a page asked for under an
    // earlier term is thrown away when it arrives
    let requestCount = 0;
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    watch(filterText, (text) => {
        clearDebounceTimer();
        debounceTimer = setTimeout(() => {
            debounceTimer = null;
            currentTerm.value = text.trim();
        }, FILTER_DEBOUNCE_MS);
    });

    watch(
        currentTerm,
        () => {
            requestCount++;
            resources.value = [];
            nextOffset.value = 0;
            isLoading.value = false;
            hasFailed.value = false;
            void loadMore();
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

    async function loadMore(): Promise<void> {
        const offset = nextOffset.value;
        if (offset === null || isLoading.value || hasFailed.value) {
            return;
        }
        const requestId = ++requestCount;
        isLoading.value = true;
        try {
            const page = await fetchRelatedResources(
                resourceId,
                rowId,
                offset,
                RELATED_RESOURCES_PAGE_SIZE,
                currentTerm.value,
            );
            if (requestId === requestCount) {
                resources.value.push(...page.resources);
                nextOffset.value = page.next_offset;
            }
        } catch {
            if (requestId === requestCount) {
                hasFailed.value = true;
            }
        } finally {
            if (requestId === requestCount) {
                isLoading.value = false;
            }
        }
    }

    async function retry(): Promise<void> {
        hasFailed.value = false;
        await loadMore();
    }

    return {
        filterText,
        currentTerm,
        resources,
        hasMore,
        isLoading,
        hasFailed,
        loadMore,
        retry,
    };
}
