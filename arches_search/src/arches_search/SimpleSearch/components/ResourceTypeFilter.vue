<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { GraphModel } from "@/arches_search/AdvancedSearch/types.ts";
import type { ResourceType } from "@/arches_search/SimpleSearch/types.ts";

const RESOURCE_TYPE_FALLBACK_KEY = "__all__";

const { $gettext, current } = useGettext();
const { toggleGraph, activeGraphs, searchResults } = useSearchFilters();

const compactCountFormatter = computed(
    () => new Intl.NumberFormat(current, { notation: "compact" }),
);
const fullCountFormatter = computed(() => new Intl.NumberFormat(current));

const resourceTypes = ref<ResourceType[]>([]);
const hasResourceTypeLoadError = ref(false);

const resourceTypeLoadErrorMessage = computed(() =>
    $gettext("Resource type filters are unavailable."),
);

const allResourceType = computed<ResourceType>(() => ({
    id: null,
    label: $gettext("All"),
    icon: "",
}));

const displayedResourceTypes = computed<ResourceType[]>(() => [
    allResourceType.value,
    ...resourceTypes.value,
]);

const resourceTypeCountsByGraphId = computed<Map<string, number>>(() => {
    const countsByGraphId = new Map<string, number>();
    for (const resourceTypeCount of searchResults.value.resource_type_counts ??
        []) {
        countsByGraphId.set(
            resourceTypeCount.graph_id,
            resourceTypeCount.count,
        );
    }
    return countsByGraphId;
});

watchEffect(async () => {
    await loadResourceTypes();
});

async function loadResourceTypes(): Promise<void> {
    try {
        hasResourceTypeLoadError.value = false;

        const graphs: GraphModel[] = await getGraphs();
        resourceTypes.value = graphs
            .filter((graph) => graph.isresource && graph.is_active)
            .map((graph) => ({
                id: graph.graphid,
                label: graph.name,
                icon: graph.iconclass,
            }));
    } catch (error) {
        console.error(error);
        resourceTypes.value = [];
        hasResourceTypeLoadError.value = true;
    }
}

function getResourceTypeButtonKey(resourceType: ResourceType): string {
    return resourceType.id ?? RESOURCE_TYPE_FALLBACK_KEY;
}

function isResourceTypeSelected(resourceType: ResourceType): boolean {
    if (resourceType.id === null) {
        return activeGraphs.value.length === 0;
    }

    return activeGraphs.value.some((graph) => graph.id === resourceType.id);
}

function selectGraph(resourceType: ResourceType): void {
    toggleGraph(resourceType);
}

function getResourceTypeCount(resourceType: ResourceType): number {
    if (resourceType.id === null) {
        return searchResults.value.all_resource_count ?? 0;
    }

    return resourceTypeCountsByGraphId.value.get(resourceType.id) ?? 0;
}

function getResourceTypeCountLabel(resourceType: ResourceType): string {
    return compactCountFormatter.value.format(
        getResourceTypeCount(resourceType),
    );
}

function getResourceTypeCountDisplay(resourceType: ResourceType): string {
    return $gettext("(%{count})", {
        count: getResourceTypeCountLabel(resourceType),
    });
}

function getResourceTypeTooltip(resourceType: ResourceType): string {
    return $gettext("%{label} — %{count} records", {
        label: resourceType.label,
        count: fullCountFormatter.value.format(
            getResourceTypeCount(resourceType),
        ),
    });
}
</script>

<template>
    <div class="resource-type-filter">
        <Button
            v-for="resourceType in displayedResourceTypes"
            :key="getResourceTypeButtonKey(resourceType)"
            class="type-btn"
            severity="secondary"
            size="large"
            type="button"
            variant="outlined"
            :class="{ active: isResourceTypeSelected(resourceType) }"
            :title="getResourceTypeTooltip(resourceType)"
            @click="selectGraph(resourceType)"
        >
            <i
                v-if="resourceType.icon"
                class="type-icon"
                :class="resourceType.icon"
            />
            <span class="type-label">{{ resourceType.label }}</span>
            <span class="type-count">{{
                getResourceTypeCountDisplay(resourceType)
            }}</span>
        </Button>

        <span
            v-if="hasResourceTypeLoadError"
            aria-live="polite"
            class="load-error"
            role="status"
        >
            {{ resourceTypeLoadErrorMessage }}
        </span>
    </div>
</template>

<style scoped>
.resource-type-filter {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.2rem 1.6rem 1.4rem;
    overflow-x: auto;
    scrollbar-width: none;
}

.resource-type-filter::-webkit-scrollbar {
    display: none;
}

.resource-type-filter .type-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center !important;
    flex-shrink: 0;
    gap: 0.5rem;
    padding: 0.7rem 1.2rem;
    border: 0.15rem solid var(--arches-search-chip-border);
    border-radius: var(--arches-search-radius-pill);
    background: var(--p-content-background);
    color: var(--arches-search-sec-btn-text) !important;
    font-size: 1.2rem;
    font-weight: 600;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
    transition:
        background 0.12s,
        border-color 0.12s,
        color 0.12s;
}

.resource-type-filter .type-btn:hover {
    background: var(--p-content-hover-background) !important;
    border: 0.15rem solid var(--p-text-muted-color) !important;
    color: var(--arches-search-sec-btn-text) !important;
}

/* color needs !important here too, purely to beat the resting rule above
   now that it's !important — this selector already outranks PrimeVue's own
   2-class outlined/secondary rule on plain specificity (3 classes vs 2). */
.resource-type-filter .type-btn.active {
    background: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color) !important;
}

.resource-type-filter .type-btn.active:hover {
    background: var(--p-primary-color) !important;
    border: 0.15rem solid var(--p-primary-color) !important;
    color: var(--p-primary-contrast-color) !important;
}

.resource-type-filter .type-btn .type-icon {
    font-size: 1.1rem;
}

.resource-type-filter .type-btn .type-count {
    margin-inline-start: 0.1rem;
    font-size: 1rem;
    font-weight: 500;
}

.resource-type-filter .load-error {
    color: var(--p-surface-500);
    font-size: var(--p-arches-search-font-size);
}
</style>
