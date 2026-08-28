<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import {
    GEOMETRY_TYPE_LINESTRING,
    GEOMETRY_TYPE_POINT,
    GEOMETRY_TYPE_POLYGON,
} from "@/arches_vue_components/components/MapComponent/constants.ts";
import { useResolvedMapContext } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";

import type { Feature } from "geojson";
import { type MapContext } from "@/arches_vue_components/components/MapComponent/types.ts";

interface AppliedFilter {
    featureId: string;
    feature: Feature;
    label: string;
    bufferSummary: string | null;
}

const { context = undefined } = defineProps<{
    context?: MapContext;
}>();

const {
    drawnFeatures,
    selectedDrawnFeature,
    selectDrawnFeature,
    deleteSelectedDrawnFeature,
    deleteAllDrawnFeatures,
} = useResolvedMapContext(context, "AppliedFiltersList");

const { $gettext } = useGettext();

const geometryKindLabels: Record<string, string> = {
    [GEOMETRY_TYPE_POINT]: $gettext("Point"),
    [GEOMETRY_TYPE_LINESTRING]: $gettext("Line"),
    [GEOMETRY_TYPE_POLYGON]: $gettext("Polygon"),
};

const listedFilters = computed<AppliedFilter[]>(() => {
    const countByGeometryType: Record<string, number> = {};

    return drawnFeatures.value.map((feature) => {
        const geometryType = feature.geometry.type;
        countByGeometryType[geometryType] =
            (countByGeometryType[geometryType] || 0) + 1;

        const kindLabel = geometryKindLabels[geometryType] ?? geometryType;
        const bufferDistance = feature.properties?.buffer_distance;
        const bufferUnits = feature.properties?.buffer_units;

        let bufferSummary: string | null = null;
        if (bufferDistance) {
            bufferSummary = $gettext("Buffer: %{distance} %{units}", {
                distance: String(bufferDistance),
                units: bufferUnits,
            });
        }

        return {
            featureId: String(feature.id),
            feature,
            label: `${kindLabel} #${countByGeometryType[geometryType]}`,
            bufferSummary,
        };
    });
});

function isSelected(featureId: string): boolean {
    return (
        selectedDrawnFeature.value !== null &&
        String(selectedDrawnFeature.value.id) === featureId
    );
}

function onSelect(appliedFilter: AppliedFilter): void {
    selectDrawnFeature(appliedFilter.feature);
}

function onRemove(appliedFilter: AppliedFilter): void {
    selectDrawnFeature(appliedFilter.feature);
    deleteSelectedDrawnFeature();
}
</script>

<template>
    <div
        v-if="listedFilters.length"
        class="applied-filters-list"
    >
        <div class="applied-filters-list-header">
            <span class="applied-filters-list-label">
                {{
                    $gettext("%{count} geometries", {
                        count: String(listedFilters.length),
                    })
                }}
            </span>
            <Button
                icon="pi pi-trash"
                icon-pos="left"
                severity="secondary"
                type="button"
                :label="$gettext('Clear all')"
                :text="true"
                @click="deleteAllDrawnFeatures"
            />
        </div>
        <ul class="applied-filters-list-items">
            <li
                v-for="(appliedFilter, index) in listedFilters"
                :key="appliedFilter.featureId"
                class="applied-filter-item"
                :class="{ active: isSelected(appliedFilter.featureId) }"
            >
                <Button
                    class="applied-filter-item-select"
                    type="button"
                    :text="true"
                    @click="onSelect(appliedFilter)"
                >
                    <span class="applied-filter-item-index"
                        >#{{ index + 1 }}</span
                    >
                    <span class="applied-filter-item-info">
                        <span class="applied-filter-item-label">{{
                            appliedFilter.label
                        }}</span>
                        <span
                            v-if="appliedFilter.bufferSummary"
                            class="applied-filter-item-sub"
                            >{{ appliedFilter.bufferSummary }}</span
                        >
                    </span>
                </Button>
                <Button
                    icon="pi pi-times"
                    severity="secondary"
                    type="button"
                    :aria-label="$gettext('Remove')"
                    :text="true"
                    @click="onRemove(appliedFilter)"
                />
            </li>
        </ul>
    </div>
</template>

<style scoped>
.applied-filters-list {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.applied-filters-list-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.applied-filters-list-label {
    font-size: 1.1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05rem;
    color: var(--p-text-muted-color);
}

.applied-filters-list-items {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    list-style: none;
    padding-inline-start: 0;
}

.applied-filter-item {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    border: 0.15rem solid var(--arches-search-card-border);
    border-radius: 0.6rem;
}

.applied-filter-item.active {
    border-color: var(--p-primary-color);
    background: var(--arches-search-primary-muted-bg);
}

.applied-filter-item-select {
    flex: 1;
    justify-content: flex-start;
    gap: 0.8rem;
    padding: 0.6rem 1rem;
    color: var(--p-text-color);
}

.applied-filter-item-index {
    flex-shrink: 0;
    padding: 0.1rem 0.6rem;
    border-radius: 0.4rem;
    background: var(--arches-search-chip-search-bg);
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-weight: 700;
}

.applied-filter-item-info {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    min-inline-size: 0;
}

.applied-filter-item-label {
    font-size: 1.2rem;
    font-weight: 600;
}

.applied-filter-item-sub {
    font-size: 1.1rem;
    color: var(--p-text-muted-color);
}
</style>
