<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import InputText from "openvue/inputtext";
import Skeleton from "openvue/skeleton";

import LoadFailedMessage from "@/arches_search/RelationshipGraph/components/LoadFailedMessage.vue";
import RelatedResourceRow from "@/arches_search/RelationshipGraph/components/RelatedResourceRow.vue";
import { useRelatedResources } from "@/arches_search/RelationshipGraph/composables/useRelatedResources.ts";

const LOADING_PLACEHOLDER_COUNT = 3;
const SCROLL_THRESHOLD_PIXELS = 72;

const { resourceId, rowId } = defineProps<{
    resourceId: string;
    rowId: string;
}>();

const { $gettext } = useGettext();
const {
    filterText,
    currentTerm,
    resources,
    hasMore,
    isLoading,
    hasFailed,
    loadMore,
    retry,
} = useRelatedResources(resourceId, rowId);

const emptyMessage = computed<string>(() => {
    if (currentTerm.value) {
        return $gettext(
            "No related resources match %{term}.",
            { term: currentTerm.value },
            true,
        );
    }
    return $gettext("No related resources to show.");
});

function onScroll(event: Event): void {
    const results = event.currentTarget as HTMLElement;
    const distanceFromBottom =
        results.scrollHeight - (results.scrollTop + results.clientHeight);
    if (distanceFromBottom > SCROLL_THRESHOLD_PIXELS) {
        return;
    }
    void loadMore();
}
</script>

<template>
    <div class="related-resource-list">
        <InputText
            v-model="filterText"
            class="filter"
            size="small"
            type="search"
            :fluid="true"
            :placeholder="$gettext('Filter by name')"
            :aria-label="$gettext('Filter the related resources by name')"
        />

        <div
            class="results"
            @scroll.passive="onScroll"
        >
            <ul
                v-if="resources.length > 0"
                class="resources"
            >
                <RelatedResourceRow
                    v-for="resource in resources"
                    :key="resource.relationship_id"
                    :resource-id="resource.resource_id"
                    :name="resource.name"
                />
            </ul>

            <div
                v-if="isLoading"
                class="loading"
            >
                <Skeleton
                    v-for="placeholder in LOADING_PLACEHOLDER_COUNT"
                    :key="placeholder"
                    class="loading-row"
                />
            </div>

            <LoadFailedMessage
                v-else-if="hasFailed"
                :message="
                    $gettext('The related resources could not be loaded.')
                "
                @retry="retry()"
            />

            <span
                v-else-if="!hasMore && resources.length === 0"
                class="message"
            >
                {{ emptyMessage }}
            </span>
        </div>
    </div>
</template>

<style scoped>
.related-resource-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding-inline-start: 2.4rem;
    padding-block-end: 0.6rem;
}

.related-resource-list .filter {
    font-size: 1.3rem;
}

.related-resource-list .results {
    max-block-size: 30rem;
    overflow-y: auto;
    /* Room for the scroll bar, so it never sits over the report button */
    scrollbar-gutter: stable;
    padding-inline-end: 0.8rem;
}

.related-resource-list .resources {
    margin: 0;
    padding: 0;
    list-style: none;
}

.related-resource-list .loading {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding-block: 0.6rem;
}

.related-resource-list .loading .loading-row {
    block-size: 2.8rem;
}

.related-resource-list .message {
    display: block;
    padding-block: 0.6rem;
    font-size: 1.3rem;
    color: var(--p-text-muted-color);
}
</style>
