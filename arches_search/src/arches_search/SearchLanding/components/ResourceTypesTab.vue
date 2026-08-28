<script setup lang="ts">
import { ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";
import { useRouter } from "vue-router";

import Button from "primevue/button";
import Skeleton from "primevue/skeleton";

import { getGraphs } from "@/arches_search/AdvancedSearch/api.ts";
import { fetchResourceTypeCounts } from "@/arches_search/SearchLanding/api.ts";
import { routeNames } from "@/arches_search/routes.ts";
import { usePendingSearchStore } from "@/arches_search/stores/usePendingSearchStore.ts";

import type { GraphModel } from "@/arches_search/AdvancedSearch/types.ts";

const MODEL_ICON_COLOR_COUNT = 8;
const PLACEHOLDER_CARD_COUNT = 6;

const { $gettext } = useGettext();
const router = useRouter();

const resourceTypes = ref<GraphModel[]>([]);
const hasLoadError = ref(false);
const resourceTypesLoading = ref(true);
const resourceTypeCounts = ref<Record<string, number | null>>({});
const resourceTypeCountsLoaded = ref(false);

watchEffect(() => {
    loadResourceTypes();
});

async function loadResourceTypes(): Promise<void> {
    try {
        hasLoadError.value = false;
        resourceTypes.value = await getGraphs();
    } catch (error) {
        console.error(error);
        resourceTypes.value = [];
        hasLoadError.value = true;
        return;
    } finally {
        resourceTypesLoading.value = false;
    }
    await loadResourceTypeCounts();
}

async function loadResourceTypeCounts(): Promise<void> {
    try {
        const counts = await fetchResourceTypeCounts();
        resourceTypeCounts.value = Object.fromEntries(
            counts.map((entry) => [entry.graphId, entry.count]),
        );
    } catch (error) {
        console.error(error);
        resourceTypeCounts.value = Object.fromEntries(
            resourceTypes.value.map((resourceType) => [
                resourceType.graphid,
                null,
            ]),
        );
    } finally {
        resourceTypeCountsLoaded.value = true;
    }
}

function onSelectResourceType(resourceType: GraphModel): void {
    usePendingSearchStore().set({ graphIds: [resourceType.graphid] });
    router.push({ name: routeNames.simpleSearch });
}

function getModelCardIconColor(resourceTypeIndex: number): string {
    const colorNumber = (resourceTypeIndex % MODEL_ICON_COLOR_COUNT) + 1;
    return `var(--arches-search-model-icon-color-${colorNumber})`;
}
</script>

<template>
    <div class="resource-types-tab">
        <div
            v-if="resourceTypesLoading"
            class="model-grid"
        >
            <div
                v-for="placeholderIndex in PLACEHOLDER_CARD_COUNT"
                :key="placeholderIndex"
                class="model-card"
            >
                <span class="model-card-header">
                    <Skeleton
                        class="model-card-icon"
                        size="3.8rem"
                    />
                    <span class="model-card-identity">
                        <Skeleton
                            width="4rem"
                            height="2.2rem"
                        />
                        <Skeleton
                            width="8rem"
                            height="1.4rem"
                        />
                    </span>
                </span>
            </div>
        </div>

        <div
            v-else
            class="model-grid"
        >
            <Button
                v-for="(resourceType, resourceTypeIndex) in resourceTypes"
                :key="resourceType.graphid"
                class="model-card"
                severity="secondary"
                type="button"
                variant="text"
                @click="onSelectResourceType(resourceType)"
            >
                <span class="model-card-header">
                    <span
                        class="model-card-icon"
                        :style="{
                            background:
                                getModelCardIconColor(resourceTypeIndex),
                        }"
                    >
                        <i
                            v-if="resourceType.iconclass"
                            :class="resourceType.iconclass"
                        />
                    </span>
                    <span class="model-card-identity">
                        <span class="model-card-count">
                            <Skeleton
                                v-if="!resourceTypeCountsLoaded"
                                width="4rem"
                                height="2.2rem"
                            />
                            <span
                                v-else-if="
                                    resourceTypeCounts[resourceType.graphid] ===
                                    null
                                "
                                class="model-card-count-unavailable"
                            >
                                {{ $gettext("Unavailable") }}
                            </span>
                            <span v-else>
                                {{ resourceTypeCounts[resourceType.graphid] }}
                            </span>
                        </span>
                        <span class="model-card-label">{{
                            resourceType.name
                        }}</span>
                    </span>
                </span>
                <span
                    v-if="resourceType.description"
                    class="model-card-desc"
                >
                    {{ resourceType.description }}
                </span>
            </Button>
        </div>

        <span
            v-if="hasLoadError"
            aria-live="polite"
            class="load-error"
            role="status"
        >
            {{ $gettext("Resource types are unavailable.") }}
        </span>
    </div>
</template>

<style scoped>
.model-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(28rem, 1fr));
    gap: 1.2rem;
}

.model-grid .model-card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    gap: 1rem;
    padding: 1.6rem 1.8rem 2.8rem;
    border: 0.15rem solid var(--arches-search-card-border);
    border-radius: var(--arches-search-model-card-radius);
    background: var(--arches-search-card-bg);
    color: var(--arches-search-sec-btn-text);
    text-align: left;
    transition:
        box-shadow 0.15s,
        transform 0.15s,
        border-color 0.15s;
}

.model-grid .model-card:hover {
    box-shadow: var(--arches-search-card-shadow-hover);
    transform: translateY(-0.2rem);
    border-color: var(--p-primary-color);
    background: var(--arches-search-card-bg);
}

.model-card-header {
    display: flex;
    align-items: center;
    gap: 1.2rem;
}

.model-card-icon {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    inline-size: 3.8rem;
    block-size: 3.8rem;
    border-radius: var(--arches-search-model-icon-radius);
    color: var(--arches-search-model-icon-text);
    font-size: 1.6rem;
}

.model-card-icon .pi {
    font-size: 1.6rem;
}

.model-card-identity {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
}

.model-card-count {
    color: var(--p-text-color);
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1;
}

.model-card-count-unavailable {
    color: var(--p-text-muted-color);
    font-size: var(--p-arches-search-font-size);
    font-weight: 600;
}

.model-card-label {
    color: var(--p-text-color);
    font-size: 1.4rem;
    font-weight: 700;
    line-height: 1.2;
    white-space: normal;
}

.model-card-desc {
    inline-size: 100%;
    padding-block-start: 1rem;
    border-block-start: 0.1rem solid var(--arches-search-card-border);
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    line-height: 1.55;
    white-space: normal;
}

.resource-types-tab .load-error {
    color: var(--p-surface-500);
    font-size: var(--p-arches-search-font-size);
}
</style>
