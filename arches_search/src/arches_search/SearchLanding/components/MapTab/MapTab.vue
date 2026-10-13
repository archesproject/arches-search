<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import MapComponent from "@/arches_vue_components/components/MapComponent/MapComponent.vue";
import SpatialFilterPanel from "@/arches_search/SearchLanding/components/MapTab/components/SpatialFilterPanel/SpatialFilterPanel.vue";

import { resolveDefaultOverlayLayers } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";
import { routeNames } from "@/arches_search/routes.ts";
import { usePendingSearchStore } from "@/arches_search/stores/usePendingSearchStore.ts";

import type { FeatureCollection } from "geojson";
import type {
    MapLayer,
    MapSettings,
} from "@/arches_vue_components/components/MapComponent/types.ts";

const LANDING_MAP_SETTINGS: Partial<MapSettings> = {
    geocoderVisible: false,
    showFullscreenControl: false,
    showCursorCoordinates: false,
    showMapScale: false,
    showZoomLevel: false,
};

const router = useRouter();

const mapFilter = ref<FeatureCollection | null>(null);

function resolveLandingOverlayLayers(
    candidateOverlayLayers: MapLayer[],
): MapLayer[] {
    return resolveDefaultOverlayLayers(candidateOverlayLayers)
        .filter((layer) => layer.is_resource_layer)
        .map((layer) => ({ ...layer, addtomap: true }));
}

function onMapUpdate(updatedValue: FeatureCollection): void {
    mapFilter.value = updatedValue.features.length > 0 ? updatedValue : null;
}

function onSearch(): void {
    if (!mapFilter.value) {
        return;
    }
    usePendingSearchStore().set({ mapFilter: mapFilter.value });
    router.push({ name: routeNames.simpleSearch });
}
</script>

<template>
    <div class="map-tab-map">
        <MapComponent
            :interaction-tools="[]"
            :settings="LANDING_MAP_SETTINGS"
            :resolve-overlay-layers="resolveLandingOverlayLayers"
            @update:value="onMapUpdate"
        >
            <template #overlay="{ context }">
                <SpatialFilterPanel
                    class="map-tab-spatial-filter"
                    :context="context"
                    @search="onSearch"
                />
            </template>
        </MapComponent>
    </div>
</template>

<style scoped>
.map-tab-map {
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    block-size: 65rem;
}

.map-tab-map :deep(.maplibregl-ctrl-top-right) {
    inset-block-start: 5rem;
}

.map-tab-spatial-filter {
    align-self: flex-end;
    inline-size: 35rem;
    max-inline-size: 100%;
    min-block-size: 0;
    margin-block: 6rem 1.6rem;
    margin-inline-end: 5rem;
}
</style>
