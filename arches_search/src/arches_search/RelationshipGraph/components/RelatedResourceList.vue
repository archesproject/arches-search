<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import InputText from "openvue/inputtext";
import Skeleton from "openvue/skeleton";

import { generateArchesURL } from "@/arches_vue_components/application";

import LoadFailedMessage from "@/arches_search/RelationshipGraph/components/LoadFailedMessage.vue";
import { useRelatedResources } from "@/arches_search/RelationshipGraph/composables/useRelatedResources.ts";

import type {
    RelatedResource,
    SelectedResource,
} from "@/arches_search/RelationshipGraph/types.ts";

const LOADING_PLACEHOLDER_COUNT = 3;
const SCROLL_THRESHOLD_PIXELS = 72;

const { resourceId, rowId } = defineProps<{
    resourceId: string;
    rowId: string;
}>();

const viewRelatedResource = inject<
    ((resource: SelectedResource) => void) | null
>("viewRelatedResource", null);

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

function reportLink(relatedResourceId: string): string {
    return generateArchesURL("arches:resource_report", {
        resourceid: relatedResourceId,
    });
}

function reportLinkLabel(name: string): string {
    return $gettext("View the report of %{name}", { name }, true);
}

function addToPanelLabel(name: string): string {
    return $gettext(
        "Show the relationships of %{name} in the panel",
        { name },
        true,
    );
}

function addToPanel(resource: RelatedResource): void {
    viewRelatedResource?.({ id: resource.resource_id, title: resource.name });
}

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
                <li
                    v-for="resource in resources"
                    :key="resource.relationship_id"
                    class="resource"
                >
                    <Button
                        v-if="viewRelatedResource"
                        class="name"
                        variant="link"
                        :label="resource.name"
                        :aria-label="addToPanelLabel(resource.name)"
                        :title="addToPanelLabel(resource.name)"
                        @click="addToPanel(resource)"
                    />
                    <span
                        v-else
                        class="name"
                        :title="resource.name"
                    >
                        {{ resource.name }}
                    </span>
                    <Button
                        as="a"
                        class="report"
                        icon="pi pi-external-link"
                        rel="noopener noreferrer"
                        target="_blank"
                        variant="link"
                        :href="reportLink(resource.resource_id)"
                        :aria-label="reportLinkLabel(resource.name)"
                        :title="reportLinkLabel(resource.name)"
                    />
                </li>
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

.related-resource-list .resource {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    min-inline-size: 0;
    padding-block: 0.2rem;
    font-size: 1.3rem;
    border-block-end: 0.0625rem solid var(--p-content-border-color);
}

.related-resource-list .resource:last-child {
    border-block-end: none;
}

.related-resource-list .resource .name {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.related-resource-list .resource span.name {
    color: var(--p-text-color);
}

.related-resource-list .resource .name.p-button {
    justify-content: flex-start;
    padding: 0;
    font-size: inherit;
}

.related-resource-list .resource .name.p-button :deep(.p-button-label) {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* A little larger than a small button, so it reads next to the name */
.related-resource-list .resource .report.p-button {
    flex-shrink: 0;
    inline-size: 2.6rem;
    block-size: 2.6rem;
}

/* The icon takes its size from the theme, not from the button */
.related-resource-list .resource .report.p-button :deep(.p-button-icon) {
    font-size: 1.2rem;
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
