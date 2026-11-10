<script setup lang="ts">
import { ref, useTemplateRef, watch } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import MapComponent from "@/arches_vue_components/components/MapComponent/MapComponent.vue";
import MapToolsPanel from "@/arches_vue_components/components/MapComponent/components/MapToolsPanel/MapToolsPanel.vue";

import { resolveDefaultOverlayLayers } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";
import { useDefaultMapInteractionTools } from "@/arches_vue_components/components/MapComponent/composables/useDefaultMapInteractionTools.ts";
import { useResultsMapFocus } from "@/arches_search/SimpleSearch/composables/useResultsMapFocus.ts";
import { useResultsMapHover } from "@/arches_search/SimpleSearch/composables/useResultsMapHover.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { SEARCH_RESULTS_SOURCE } from "@/arches_search/SimpleSearch/types.ts";

import type { FeatureCollection } from "geojson";
import type { VectorTileSource } from "maplibre-gl";

import type { MapLayer } from "@/arches_vue_components/components/MapComponent/types.ts";

const UPDATE_MODEL_VALUE_EVENT = "update:modelValue" as const;
const REMOVE_EVENT = "remove" as const;
const CLOSE_EVENT = "close" as const;

const { modelValue } = defineProps<{
    modelValue: FeatureCollection | null;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_MODEL_VALUE_EVENT, value: FeatureCollection): void;
    (event: typeof REMOVE_EVENT): void;
    (event: typeof CLOSE_EVENT): void;
}>();

const { resultsTileUrl } = useSearchFilters();
const { $gettext } = useGettext();

const mapToolsTool = useDefaultMapInteractionTools().find(
    (tool) => tool.component === MapToolsPanel,
);

const mapComponentRef =
    useTemplateRef<InstanceType<typeof MapComponent>>("mapComponent");
const isMapReady = ref(false);

const { addResultsHoverLayers, listenForResultsHover } =
    useResultsMapHover(mapComponentRef);
useResultsMapFocus(mapComponentRef, isMapReady);

watch(resultsTileUrl, setSearchTiles);

watch(
    () => modelValue,
    (updatedModelValue) => {
        const context = mapComponentRef.value?.context;
        if (!isMapReady.value || !context) {
            return;
        }

        const updatedFeatures = updatedModelValue?.features ?? [];
        const updatedGeometries = JSON.stringify(
            updatedFeatures.map((feature) => feature.geometry),
        );
        const drawnGeometries = JSON.stringify(
            context.drawnFeatures.value.map((feature) => feature.geometry),
        );
        if (updatedGeometries === drawnGeometries) {
            return;
        }

        if (context.drawnFeatures.value.length > 0) {
            context.deleteAllDrawnFeatures();
        }
        if (updatedFeatures.length > 0) {
            context.addFeatures(updatedFeatures);
        }
    },
);

function onMapReady(): void {
    if (mapToolsTool) {
        mapComponentRef.value?.openPanel(mapToolsTool.name);
    }
    if (modelValue && modelValue.features.length > 0) {
        mapComponentRef.value?.context?.addFeatures(modelValue.features);
    }
    listenForResultsHover();
    isMapReady.value = true;
}

function onOverlaysUpdated(): void {
    addResultsHoverLayers();
    void setSearchTiles();
}

async function setSearchTiles(): Promise<void> {
    const map = mapComponentRef.value?.map;
    if (!map) {
        return;
    }
    if (!map.areTilesLoaded()) {
        await map.once("idle");
    }
    if (resultsTileUrl.value) {
        map
            .getSource<VectorTileSource>(SEARCH_RESULTS_SOURCE)
            ?.setTiles([resultsTileUrl.value]);
    }
}

function resolveSearchOverlayLayers(
    candidateOverlayLayers: MapLayer[],
): MapLayer[] {
    const searchOnlyOverlays = candidateOverlayLayers.filter(
        (layer) =>
            layer.isoverlay && layer.activated !== false && layer.searchonly,
    );
    const hiddenDefaultOverlays = resolveDefaultOverlayLayers(
        candidateOverlayLayers,
    ).map((layer) => ({ ...layer, addtomap: false }));
    return [...searchOnlyOverlays, ...hiddenDefaultOverlays];
}

function onMapUpdate(updatedValue: FeatureCollection): void {
    if (updatedValue.features.length === 0) {
        emit(REMOVE_EVENT);
    } else {
        emit(UPDATE_MODEL_VALUE_EVENT, updatedValue);
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
            <Button
                icon="pi pi-times"
                icon-pos="left"
                class="map-filter-close-btn"
                :label="$gettext('Close')"
                :text="true"
                @click="emit(CLOSE_EVENT)"
            />
        </div>
        <MapComponent
            ref="mapComponent"
            :value="modelValue"
            :resolve-overlay-layers="resolveSearchOverlayLayers"
            :open-popups-inside-drawn-shapes="true"
            @update:overlays="onOverlaysUpdated"
            @update:value="onMapUpdate"
            @ready="onMapReady"
        />
    </div>
</template>

<style scoped>
.search-map-filter-panel {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    background-color: var(--p-content-background);
    font-size: 1rem;
    line-height: 1.45;
}

.map-filter-header {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: space-between;
    padding-block: 2rem 0.75rem;
    padding-inline: 2rem;
    border-block-end: 0.125rem solid var(--p-content-border-color);
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
</style>
