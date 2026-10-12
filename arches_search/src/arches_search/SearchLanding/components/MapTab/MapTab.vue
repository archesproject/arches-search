<script setup lang="ts">
import { ref, useTemplateRef } from "vue";
import { useRouter } from "vue-router";

import { useGettext } from "vue3-gettext";

import MapComponent from "@/arches_vue_components/components/MapComponent/MapComponent.vue";
import MapToolsPanel from "@/arches_vue_components/components/MapComponent/components/MapToolsPanel/MapToolsPanel.vue";
import SpatialFilterPanel from "@/arches_search/SearchLanding/components/MapTab/components/SpatialFilterPanel.vue";

import { useDefaultMapInteractionTools } from "@/arches_vue_components/components/MapComponent/composables/useDefaultMapInteractionTools.ts";
import { routeNames } from "@/arches_search/routes.ts";
import { usePendingSearchStore } from "@/arches_search/stores/usePendingSearchStore.ts";

import type { FeatureCollection } from "geojson";
import type { MapInteractionTool } from "@/arches_vue_components/components/MapComponent/types.ts";

const router = useRouter();

const mapComponentRef =
    useTemplateRef<InstanceType<typeof MapComponent>>("mapComponent");

const { $gettext } = useGettext();

const spatialFilterTool: MapInteractionTool = {
    name: $gettext("Spatial filter"),
    header: $gettext("Spatial filter"),
    component: SpatialFilterPanel,
    icon: "pi pi-map-marker",
    props: { onSearch },
    badgeCount: (context) => context.drawnFeatures.value.length,
    wide: true,
};
const interactionTools = [
    spatialFilterTool,
    ...useDefaultMapInteractionTools().filter(
        (tool) => tool.component !== MapToolsPanel,
    ),
];

const mapFilter = ref<FeatureCollection | null>(null);

function openSpatialFilter(): void {
    mapComponentRef.value?.openPanel(spatialFilterTool.name);
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
            ref="mapComponent"
            :interaction-tools="interactionTools"
            @update:value="onMapUpdate"
            @ready="openSpatialFilter"
        />
    </div>
</template>

<style scoped>
.map-tab-map {
    position: relative;
    display: flex;
    flex-direction: column;
    inline-size: 100%;
    max-inline-size: 120rem;
    block-size: 64rem;
    overflow: hidden;
    border: 0.15rem solid var(--arches-search-card-border);
    border-radius: 1.2rem;
}
</style>
