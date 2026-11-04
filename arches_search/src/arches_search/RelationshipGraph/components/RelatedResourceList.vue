<script setup lang="ts">
import {
    inject,
    onBeforeUnmount,
    onMounted,
    ref,
    useTemplateRef,
    watch,
} from "vue";
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
const FILTER_DELAY_MS = 300;

const { resourceId, rowId } = defineProps<{
    resourceId: string;
    rowId: string;
}>();

const { $gettext } = useGettext();

// What is typed, and the term it settles on once typing pauses
const filterText = ref("");
const term = ref("");
let filterTimer: ReturnType<typeof setTimeout> | undefined;

watch(filterText, (text) => {
    clearTimeout(filterTimer);
    filterTimer = setTimeout(() => (term.value = text), FILTER_DELAY_MS);
});

const { resources, hasMore, isLoading, hasFailed, currentTerm, loadMore } =
    useRelatedResources(resourceId, rowId, term);

function reportLink(relatedResourceId: string): string {
    return generateArchesURL("arches:resource_report", {
        resourceid: relatedResourceId,
    });
}

function reportLinkLabel(name: string): string {
    return $gettext("View the report of %{name}", { name });
}

const viewRelatedResource = inject<
    ((resource: SelectedResource) => void) | null
>("viewRelatedResource", null);

function addToPanelLabel(name: string): string {
    return $gettext("Show the relationships of %{name} in the panel", {
        name,
    });
}

function addToPanel(resource: RelatedResource): void {
    viewRelatedResource?.({ id: resource.resource_id, title: resource.name });
}

const list = useTemplateRef<HTMLElement>("list");
const sentinel = useTemplateRef<HTMLElement>("sentinel");

let observer: IntersectionObserver | undefined;
let isSentinelVisible = false;

onMounted(() => {
    void loadMore();
    if (!list.value || !sentinel.value) return;
    observer = new IntersectionObserver(
        ([entry]) => {
            isSentinelVisible = entry.isIntersecting;
            if (isSentinelVisible) void loadMore();
        },
        { root: list.value, rootMargin: "0% 0% 100% 0%" },
    );
    observer.observe(sentinel.value);
});

// A new term lists from the start, so the list scrolls back to the top
watch(currentTerm, () => {
    if (list.value) list.value.scrollTop = 0;
});

watch(isLoading, (loading) => {
    if (!loading && isSentinelVisible && hasMore.value && !hasFailed.value) {
        void loadMore();
    }
});

onBeforeUnmount(() => {
    observer?.disconnect();
    clearTimeout(filterTimer);
});
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
            ref="list"
            class="results"
        >
            <ul
                v-if="resources.length"
                class="resources"
            >
                <li
                    v-for="resource in resources"
                    :key="resource.relationship_id"
                    class="resource"
                >
                    <button
                        v-if="viewRelatedResource"
                        type="button"
                        class="name"
                        :aria-label="addToPanelLabel(resource.name)"
                        :title="addToPanelLabel(resource.name)"
                        @click="addToPanel(resource)"
                    >
                        {{ resource.name }}
                    </button>
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
                :aria-label="$gettext('Loading related resources')"
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
                @retry="loadMore()"
            />

            <span
                v-else-if="!hasMore && !resources.length"
                class="message"
            >
                {{
                    currentTerm
                        ? $gettext("No related resources match %{term}.", {
                              term: currentTerm,
                          })
                        : $gettext("No related resources to show.")
                }}
            </span>

            <div
                ref="sentinel"
                class="sentinel"
            />
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

/* Stays above the results, so it does not scroll away with them */
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
    padding: 0.2rem 0;
    font-size: 1.3rem;
    border-block-end: 0.0625rem solid var(--p-content-border-color);
}

.related-resource-list .resource:last-child {
    border-block-end: none;
}

.related-resource-list .resource .name {
    flex: 1;
    min-inline-size: 0;
    margin: 0;
    padding: 0;
    border: none;
    background: none;
    color: var(--p-text-color);
    font: inherit;
    text-align: start;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.related-resource-list .resource button.name {
    color: var(--p-primary-color);
    cursor: pointer;
}

.related-resource-list .resource button.name:hover {
    text-decoration: underline;
}

.related-resource-list .resource button.name:focus-visible {
    outline: 0.125rem solid var(--p-focus-ring-color);
    outline-offset: 0.1rem;
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

.related-resource-list .sentinel {
    block-size: 0.0625rem;
}
</style>
