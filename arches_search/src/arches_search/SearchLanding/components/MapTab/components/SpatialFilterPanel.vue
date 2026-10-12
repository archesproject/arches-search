<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import MapToolsPanel from "@/arches_vue_components/components/MapComponent/components/MapToolsPanel/MapToolsPanel.vue";

import { useResolvedMapContext } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";

import type { MapContext } from "@/arches_vue_components/components/MapComponent/types.ts";

const SEARCH_EVENT = "search" as const;

const { context = undefined } = defineProps<{
    context?: MapContext;
}>();

const emit = defineEmits<{
    (event: typeof SEARCH_EVENT): void;
}>();

const resolvedContext = useResolvedMapContext(context, "SpatialFilterPanel");
const { drawnFeatures } = resolvedContext;

const { $gettext } = useGettext();
</script>

<template>
    <div class="spatial-filter-panel">
        <MapToolsPanel
            class="spatial-filter-tools"
            :context="resolvedContext"
        />
        <div class="spatial-filter-actions">
            <Button
                icon="pi pi-search"
                size="small"
                :label="$gettext('Search with this filter')"
                :disabled="drawnFeatures.length === 0"
                :fluid="true"
                @click="emit(SEARCH_EVENT)"
            />
        </div>
    </div>
</template>

<style scoped>
.spatial-filter-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
}

.spatial-filter-tools {
    flex: 1;
    min-height: 0;
}

.spatial-filter-actions {
    flex: 0 0 auto;
    padding-block: 1.1rem;
    padding-inline: 1.3rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
}
</style>
