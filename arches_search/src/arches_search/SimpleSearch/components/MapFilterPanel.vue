<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import MapWidget from "@/arches_component_lab/widgets/MapWidget/MapWidget.vue";

import type { FeatureCollection } from "geojson";
import type { GeoJSONFeatureCollectionValue } from "@/arches_component_lab/datatypes/geojson-feature-collection/types";

const { $gettext } = useGettext();

const props = defineProps<{
    modelValue: FeatureCollection | null;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: FeatureCollection): void;
}>();

const aliasedNodeData = (): GeoJSONFeatureCollectionValue | null => {
    if (!props.modelValue) return null;
    return {
        display_value: "",
        node_value: props.modelValue,
        details: [],
    };
};

function onEditorUpdate(
    value: GeoJSONFeatureCollectionValue | FeatureCollection,
) {
    const fc =
        "node_value" in value
            ? (value as GeoJSONFeatureCollectionValue).node_value
            : (value as FeatureCollection);
    if (fc) {
        emit("update:modelValue", fc);
    }
}
</script>

<template>
    <div class="search-map-filter-panel">
        <div class="map-filter-header">
            <h3 class="map-filter-title">
                {{ $gettext("Map Filter") }}
            </h3>
        </div>
        <MapWidget
            mode="edit"
            :aliased-node-data="aliasedNodeData()"
            @update:value="onEditorUpdate"
        />
    </div>
</template>

<style scoped>
.search-map-filter-panel {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    padding: 2rem;
    padding-inline-end: 0;
    height: 100%;
    box-sizing: border-box;
    background-color: var(--p-content-background);
    font-size: 1rem;
    line-height: 1.45;
}

.map-filter-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 0.75rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.map-filter-title {
    margin: 0;
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--p-text-color);
}
</style>
