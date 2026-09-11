<script setup lang="ts">
import { nextTick, useTemplateRef, watch } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import MapComponent from "@/arches_vue_components/components/MapComponent/MapComponent.vue";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { FeatureCollection } from "geojson";

const SEARCH_RESULTS_SOURCE = "arches-search-results";
const REMOVE_EVENT = "remove" as const;
const CLOSE_EVENT = "close" as const;

const { modelValue, visible } = defineProps<{
    modelValue: FeatureCollection | null;
    visible?: boolean;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: FeatureCollection): void;
    (event: "remove"): void;
    (event: "close"): void;
}>();

const { resultsTileUrl } = useSearchFilters();
const { $gettext } = useGettext();

const mapComponentRef =
    useTemplateRef<InstanceType<typeof MapComponent>>("mapComponent");

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

watch(
    () => modelValue,
    (updatedModelValue, previousModelValue) => {
        const previousFeatureCount = previousModelValue?.features.length ?? 0;
        const updatedFeatureCount = updatedModelValue?.features.length ?? 0;

        if (previousFeatureCount > 0 && updatedFeatureCount === 0) {
            mapComponentRef.value?.context?.deleteAllDrawnFeatures();
        }
    },
);

function onMapReady(): void {
    if (modelValue && modelValue.features.length > 0) {
        mapComponentRef.value?.context?.addFeatures(modelValue.features);
    }
}

function onOverlaysUpdate(): void {
    requestAnimationFrame(() => {
        nextTick(() => setSearchTiles(resultsTileUrl.value));
    });
}

function setSearchTiles(tileUrl: string | null): void {
    if (!tileUrl) return;
    const source = mapComponentRef.value?.map?.getSource(SEARCH_RESULTS_SOURCE);
    if (!source) return;
    (source as unknown as { setTiles: (tiles: string[]) => void }).setTiles([
        tileUrl,
    ]);
}

function onMapUpdate(updatedValue: FeatureCollection): void {
    if (updatedValue.features.length === 0) {
        emit(REMOVE_EVENT);
    } else {
        emit("update:modelValue", updatedValue);
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
            @update:overlays="onOverlaysUpdate"
            @update:value="onMapUpdate"
            @ready="onMapReady"
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
    padding-block-end: 0.75rem;
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
