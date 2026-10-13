<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import {
    FEET,
    KILOMETERS,
    MILES,
} from "@/arches_vue_components/components/MapComponent/constants.ts";
import { useResolvedMapContext } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";

import type { Feature } from "geojson";
import type { MapContext } from "@/arches_vue_components/components/MapComponent/types.ts";

const {
    feature,
    position,
    label,
    isSelected,
    context = undefined,
} = defineProps<{
    feature: Feature;
    position: number;
    label: string;
    isSelected: boolean;
    context?: MapContext;
}>();

const { selectDrawnFeature, deleteDrawnFeature, fitToFeatures } =
    useResolvedMapContext(context, "SpatialFilterRow");

const { $gettext } = useGettext();

const bufferSummary = computed<string | null>(() => {
    const bufferDistance = feature.properties?.buffer_distance;
    if (!bufferDistance) {
        return null;
    }

    const parameters = { distance: String(bufferDistance) };

    switch (feature.properties?.buffer_units) {
        case KILOMETERS:
            return $gettext("Buffer: %{distance} kilometers", parameters);
        case FEET:
            return $gettext("Buffer: %{distance} feet", parameters);
        case MILES:
            return $gettext("Buffer: %{distance} miles", parameters);
        default:
            return $gettext("Buffer: %{distance} meters", parameters);
    }
});

function selectFeature(): void {
    selectDrawnFeature(feature);
    fitToFeatures([feature]);
}
</script>

<template>
    <div
        class="spatial-filter-row"
        :class="{ 'spatial-filter-row-selected': isSelected }"
    >
        <Button
            class="spatial-filter-row-select"
            :text="true"
            :aria-pressed="isSelected"
            @click="selectFeature"
        >
            <span class="spatial-filter-row-position">#{{ position }}</span>
            <span class="spatial-filter-row-info">
                <span
                    class="spatial-filter-row-label"
                    :title="label"
                >
                    {{ label }}
                </span>
                <span
                    v-if="bufferSummary"
                    class="spatial-filter-row-buffer"
                >
                    {{ bufferSummary }}
                </span>
            </span>
        </Button>
        <Button
            class="spatial-filter-row-delete"
            icon="pi pi-times"
            severity="secondary"
            size="small"
            :text="true"
            :title="$gettext('Remove')"
            :aria-label="$gettext('Remove %{label}', { label })"
            @click="deleteDrawnFeature(feature)"
        />
    </div>
</template>

<style scoped>
.spatial-filter-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding-inline-end: 0.4rem;
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.6rem;
    background: var(--p-content-background);
}

.spatial-filter-row:hover {
    border-color: var(--p-primary-color);
    background: var(--arches-search-primary-muted-bg);
}

.spatial-filter-row-selected {
    border-color: var(--p-primary-color);
    background: var(--p-highlight-background);
}

.spatial-filter-row-select {
    flex: 1;
    justify-content: flex-start;
    gap: 0.8rem;
    min-inline-size: 0;
    padding-block: 0.6rem;
    padding-inline: 1rem;
    color: var(--p-text-color);
    text-align: start;
}

.spatial-filter-row-position {
    flex-shrink: 0;
    padding-block: 0.1rem;
    padding-inline: 0.6rem;
    border-radius: 0.4rem;
    background: var(--p-content-border-color);
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-weight: 700;
}

.spatial-filter-row-selected .spatial-filter-row-position {
    background: var(--p-primary-color);
    color: var(--p-primary-contrast-color);
}

.spatial-filter-row-info {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 0.1rem;
    min-inline-size: 0;
}

.spatial-filter-row-label {
    overflow: hidden;
    font-size: 1.2rem;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.spatial-filter-row-buffer {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
}

.spatial-filter-row-delete {
    flex-shrink: 0;
    inline-size: 2.4rem;
    block-size: 2.4rem;
    padding: 0;
}

.spatial-filter-row-delete:hover {
    --p-button-text-secondary-color: var(--p-button-text-danger-color);
    --p-button-text-secondary-hover-background: var(
        --p-button-text-danger-hover-background
    );
}
</style>
