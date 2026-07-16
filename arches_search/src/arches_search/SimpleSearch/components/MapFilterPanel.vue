<script setup lang="ts">
import { nextTick, useTemplateRef, watch } from "vue";

import { useGettext } from "vue3-gettext";

import MapWidget from "@/arches_vue_components/widgets/MapWidget/MapWidget.vue";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { FeatureCollection } from "geojson";
import type { GeoJSONFeatureCollectionAliasedNodeData } from "@/arches_vue_components/datatypes/geojson-feature-collection/types";

const SEARCH_RESULTS_SOURCE = "arches-search-results";
const SEARCH_RENDER_CONTEXT = "search";

const { modelValue, visible } = defineProps<{
    modelValue: FeatureCollection | null;
    visible?: boolean;
}>();

const { resultsTileUrl } = useSearchFilters();

const emit = defineEmits<{
    (event: "update:modelValue", value: FeatureCollection): void;
    (event: "remove"): void;
}>();

const { $gettext } = useGettext();

const mapWidgetRef =
    useTemplateRef<InstanceType<typeof MapWidget>>("mapWidget");

watch(resultsTileUrl, (tileUrl) => setSearchTiles(tileUrl));

watch(
    () => visible,
    (isVisible) => {
        if (isVisible) {
            nextTick(() => {
                mapWidgetRef.value?.map?.resize();
            });
        }
    },
);

function onOverlaysUpdate() {
    requestAnimationFrame(() => {
        nextTick(() => setSearchTiles(resultsTileUrl.value));
    });
}

function setSearchTiles(tileUrl: string | null) {
    if (!tileUrl) return;
    const source = mapWidgetRef.value?.map?.getSource(SEARCH_RESULTS_SOURCE);
    if (!source) return;
    (source as unknown as { setTiles: (tiles: string[]) => void }).setTiles([
        tileUrl,
    ]);
}

function aliasedNodeData(): GeoJSONFeatureCollectionAliasedNodeData | null {
    if (!modelValue) return null;
    return { display_value: "", node_value: modelValue, details: [] };
}

function onEditorUpdate(
    updatedValue: GeoJSONFeatureCollectionAliasedNodeData | FeatureCollection,
) {
    let featureCollection: FeatureCollection | null;
    if ("node_value" in updatedValue) {
        featureCollection = (
            updatedValue as GeoJSONFeatureCollectionAliasedNodeData
        ).node_value;
    } else {
        featureCollection = updatedValue as FeatureCollection;
    }

    if (!featureCollection || featureCollection.features.length === 0) {
        emit("remove");
    } else {
        emit("update:modelValue", featureCollection);
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
            ref="mapWidget"
            mode="edit"
            :render-context="SEARCH_RENDER_CONTEXT"
            :aliased-node-data="aliasedNodeData()"
            @update:overlays="onOverlaysUpdate"
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
