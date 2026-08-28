<script setup lang="ts">
import { computed, ref } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import AppliedFiltersList from "@/arches_search/SearchLanding/tabs/components/SpatialFilterTool/components/AppliedFiltersList.vue";
import BufferDistanceControls from "@/arches_search/SearchLanding/tabs/components/SpatialFilterTool/components/BufferDistanceControls.vue";
import DrawTypeButtons from "@/arches_search/SearchLanding/tabs/components/SpatialFilterTool/components/DrawTypeButtons.vue";

import { useResolvedMapContext } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";

import type { MapContext } from "@/arches_vue_components/components/MapComponent/types.ts";

const SEARCH_EVENT = "search" as const;

const { context = undefined } = defineProps<{
    context?: MapContext;
}>();

const emit = defineEmits<{
    (event: typeof SEARCH_EVENT): void;
}>();

const resolvedContext = useResolvedMapContext(context, "SpatialFilterTool");
const { $gettext } = useGettext();

const isPanelOpen = ref(true);

const appliedFilterCount = computed(
    () => resolvedContext.drawnFeatures.value.length,
);
</script>

<template>
    <Button
        v-if="!isPanelOpen"
        class="spatial-filter-trigger"
        icon="pi pi-map-marker"
        severity="secondary"
        type="button"
        :aria-label="$gettext('Spatial filter')"
        :badge="appliedFilterCount > 0 ? String(appliedFilterCount) : undefined"
        :rounded="true"
        @click="isPanelOpen = true"
    />
    <div
        v-else
        class="spatial-filter-panel"
    >
        <div class="spatial-filter-toolbar">
            <i class="pi pi-map-marker" />

            <span class="spatial-filter-title">{{
                $gettext("Spatial filter")
            }}</span>

            <Button
                icon="pi pi-times"
                icon-pos="left"
                severity="secondary"
                size="small"
                type="button"
                variant="outlined"
                :label="$gettext('Close')"
                @click="isPanelOpen = false"
            />
        </div>

        <AppliedFiltersList :context="resolvedContext" />

        <div class="spatial-filter-draw">
            <DrawTypeButtons :context="resolvedContext" />
            <BufferDistanceControls :context="resolvedContext" />
        </div>

        <Button
            class="spatial-filter-search-btn"
            icon="pi pi-search"
            icon-pos="left"
            type="button"
            :disabled="appliedFilterCount === 0"
            :fluid="true"
            :label="$gettext('Search with this filter')"
            @click="emit(SEARCH_EVENT)"
        />
    </div>
</template>

<style scoped>
.spatial-filter-trigger {
    position: absolute;
    inset-block-start: 1.6rem;
    inset-inline-end: 1.6rem;
    z-index: 1;
    box-shadow: var(--arches-search-card-shadow-hover);
}

.spatial-filter-panel {
    position: absolute;
    inset-block-start: 1.6rem;
    inset-inline-end: 1.6rem;
    z-index: 1;
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    inline-size: 30rem;
    max-block-size: 90%;
    padding: 1.2rem;
    overflow-y: auto;
    border: 0.15rem solid var(--arches-search-card-border);
    border-radius: 0.8rem;
    background: var(--p-content-background);
    box-shadow: var(--arches-search-card-shadow-hover);
}

.spatial-filter-toolbar {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding-block-end: 1rem;
    border-block-end: 0.15rem solid var(--arches-search-card-border);
}

.spatial-filter-toolbar .pi-map-marker {
    color: var(--p-primary-color);
    font-size: 1.4rem;
}

.spatial-filter-title {
    flex: 1;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--p-primary-color);
}

.spatial-filter-draw {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding-block-start: 0.4rem;
    padding-block-end: 0.4rem;
    border-block-start: 0.15rem solid var(--arches-search-card-border);
    border-block-end: 0.15rem solid var(--arches-search-card-border);
}

.spatial-filter-search-btn {
    justify-content: center;
}
</style>
