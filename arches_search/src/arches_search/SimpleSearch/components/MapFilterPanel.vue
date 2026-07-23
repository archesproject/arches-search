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
    (event: "close"): void;
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
            <span class="map-filter-title">
                <i class="pi pi-map" />
                {{ $gettext("Map Filter") }}
            </span>
            <button
                class="map-filter-close-btn"
                @click="emit('close')"
            >
                <i class="pi pi-times" />
                {{ $gettext("Close") }}
            </button>
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
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 0.75rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.map-filter-title {
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--p-text-color);
}

.map-filter-title .pi {
    margin-inline-end: 0.6rem;
    color: var(--p-primary-color);
}

.map-filter-close-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.8rem;
    font-family: inherit;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--p-text-muted-color);
    background: none;
    border: none;
    border-radius: 0.4rem;
    cursor: pointer;
    transition: background 0.12s;
}

.map-filter-close-btn:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}
</style>
