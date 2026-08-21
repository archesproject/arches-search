<script setup lang="ts">
import { computed, nextTick, useTemplateRef, watch } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Panel from "primevue/panel";

import {
    BufferControls,
    DrawControls,
    MapComponent,
    resolveDefaultOverlayLayers,
    ShapefileDropZone,
} from "@/arches_vue_components/components";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { FeatureCollection } from "geojson";
import type { MapLayer } from "@/arches_vue_components/components";

const SEARCH_RESULTS_SOURCE = "arches-search-results";
const MAX_DRAWN_FEATURES = 1;

function resolveOverlayLayersWithSearchResults(
    candidateOverlayLayers: MapLayer[],
): MapLayer[] {
    return [
        ...resolveDefaultOverlayLayers(candidateOverlayLayers),
        ...candidateOverlayLayers.filter((layer) => layer.searchonly),
    ];
}

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

const mapComponentRef =
    useTemplateRef<InstanceType<typeof MapComponent>>("mapComponent");

// Simple Search renders ShapefileDropZone/BufferControls/DrawControls above
// and over MapComponent rather than nested inside it, so they need its
// MapContext passed explicitly instead of picking it up via provide/inject.
const mapContext = computed(() => mapComponentRef.value?.context);

watch(resultsTileUrl, (tileUrl) => setSearchTiles(tileUrl));

watch(
    () => visible,
    (isVisible) => {
        if (isVisible) {
            nextTick(() => {
                mapComponentRef.value?.map?.resize();
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
    const source = mapComponentRef.value?.map?.getSource(SEARCH_RESULTS_SOURCE);
    if (!source) return;
    (source as unknown as { setTiles: (tiles: string[]) => void }).setTiles([
        tileUrl,
    ]);
}

function onValueUpdate(updatedValue: FeatureCollection) {
    if (updatedValue.features.length === 0) {
        emit("remove");
    } else {
        emit("update:modelValue", updatedValue);
    }
}

function clearDrawnFeatures() {
    mapContext.value?.deleteAllDrawnFeatures();
}
</script>

<template>
    <div class="search-map-filter-panel">
        <div class="map-filter-header">
            <span class="map-filter-title">
                <i class="pi pi-map" />
                {{ $gettext("Map Filter") }}
            </span>
            <Button
                :label="$gettext('Close')"
                icon="pi pi-times"
                icon-pos="left"
                :text="true"
                class="map-filter-close-btn"
                @click="emit('close')"
            />
        </div>
        <!--
        Superseded by the interaction-tools="[]" + floating-draw-panel setup
        below -- kept here, commented out, pending follow-up on this pass.
        <MapComponent
            ref="mapComponent"
            :value="modelValue"
            :overlay-layers="resolveOverlayLayersWithSearchResults"
            @update:overlays="onOverlaysUpdate"
            @update:value="onValueUpdate"
        />
        -->
        <div
            v-if="mapContext"
            class="map-tools-bar"
        >
            <ShapefileDropZone :context="mapContext" />
            <BufferControls :context="mapContext" />
        </div>
        <div class="map-area">
            <MapComponent
                ref="mapComponent"
                :value="modelValue"
                :overlay-layers="resolveOverlayLayersWithSearchResults"
                :max-features="MAX_DRAWN_FEATURES"
                :interaction-tools="[]"
                @update:overlays="onOverlaysUpdate"
                @update:value="onValueUpdate"
            />
            <Panel
                v-if="mapContext"
                class="floating-draw-panel"
                :header="$gettext('Draw')"
            >
                <div class="floating-draw-panel-content">
                    <DrawControls :context="mapContext" />
                    <Button
                        :label="$gettext('Remove All')"
                        severity="secondary"
                        @click="clearDrawnFeatures"
                    />
                </div>
            </Panel>
        </div>
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
    padding: 0.3rem 0.8rem;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--p-text-muted-color);
    border-radius: 0.4rem;
}

.map-filter-close-btn:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.map-tools-bar {
    display: flex;
    flex-direction: row;
    gap: 1.25rem;
}

.map-tools-bar > * {
    flex: 1 1 0;
}

.map-area {
    position: relative;
    display: flex;
    flex: 1;
    min-height: 0;
}

.floating-draw-panel {
    position: absolute;
    inset-block-start: 1.25rem;
    inset-inline-end: 1.25rem;
    z-index: 1;
    width: 22rem;
}

.floating-draw-panel-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
</style>
