<script setup lang="ts">
import { computed, ref, useTemplateRef } from "vue";
import { useRouter } from "vue-router";

import MapComponent from "@/arches_vue_components/components/MapComponent/MapComponent.vue";
import SpatialFilterTool from "@/arches_search/SearchLanding/components/MapTab/components/SpatialFilterTool/SpatialFilterTool.vue";

import { routeNames } from "@/arches_search/routes.ts";
import { usePendingSearchStore } from "@/arches_search/stores/usePendingSearchStore.ts";

import type { FeatureCollection } from "geojson";
import type { MapInteractionTool } from "@/arches_vue_components/components/MapComponent/types.ts";

const NO_INTERACTION_TOOLS: MapInteractionTool[] = [];

const router = useRouter();

const mapComponentRef =
    useTemplateRef<InstanceType<typeof MapComponent>>("mapComponent");

const mapFilter = ref<FeatureCollection | null>(null);

const mapContext = computed(() => mapComponentRef.value?.context ?? null);

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
            :value="mapFilter"
            :interaction-tools="NO_INTERACTION_TOOLS"
            @update:value="onMapUpdate"
        />
        <SpatialFilterTool
            v-if="mapContext"
            :context="mapContext"
            @search="onSearch"
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
