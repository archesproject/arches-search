<script setup lang="ts">
import { computed, ref } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import InputNumber from "openvue/inputnumber";
import Select from "openvue/select";

import ToolButtonGroup from "@/arches_vue_components/components/MapComponent/components/MapToolsPanel/components/ToolButtonGroup.vue";
import SpatialFilterRow from "@/arches_search/SearchLanding/components/MapTab/components/SpatialFilterPanel/components/SpatialFilterRow.vue";

import {
    DEFAULT_BUFFER_DISTANCE,
    FEET,
    KILOMETERS,
    LINE,
    METERS,
    MILES,
    POINT,
    POLYGON,
} from "@/arches_vue_components/components/MapComponent/constants.ts";
import { useGeometryKindOptions } from "@/arches_vue_components/components/MapComponent/components/MapToolsPanel/composables/useGeometryKindOptions.ts";
import { useResolvedMapContext } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";
import { useSpatialFilterLabels } from "@/arches_search/SearchLanding/components/MapTab/components/SpatialFilterPanel/composables/useSpatialFilterLabels.ts";

import type {
    DrawMode,
    MapContext,
} from "@/arches_vue_components/components/MapComponent/types.ts";

const SEARCH_EVENT = "search" as const;

const { context = undefined } = defineProps<{
    context?: MapContext;
}>();

const emit = defineEmits<{
    (event: typeof SEARCH_EVENT): void;
}>();

const resolvedContext = useResolvedMapContext(context, "SpatialFilterPanel");
const {
    drawnFeatures,
    selectedDrawnFeature,
    activeDrawMode,
    allowedGeometryTypes,
    setDrawMode,
    deselectDrawnFeature,
    deleteAllDrawnFeatures,
    setBufferForSelectedFeature,
} = resolvedContext;

const { $gettext, $ngettext } = useGettext();

const geometryKindOptions = useGeometryKindOptions(allowedGeometryTypes);
const labelsByFeatureId = useSpatialFilterLabels(drawnFeatures);

const bufferUnitOptions = [
    { label: $gettext("Meters"), value: METERS },
    { label: $gettext("Kilometers"), value: KILOMETERS },
    { label: $gettext("Feet"), value: FEET },
    { label: $gettext("Miles"), value: MILES },
];

const isDrawOpen = ref(true);
const bufferDistance = ref<number | null>(DEFAULT_BUFFER_DISTANCE);
const bufferUnits = ref<string>(METERS);

const geometryCountLabel = computed(() =>
    $ngettext(
        "%{count} geometry",
        "%{count} geometries",
        drawnFeatures.value.length,
        { count: String(drawnFeatures.value.length) },
    ),
);

const drawHint = computed(() => {
    if (activeDrawMode.value === POINT) {
        return $gettext("Click on the map to place a point.");
    }
    if (activeDrawMode.value === LINE) {
        return $gettext("Click to add vertices. Double-click to finish.");
    }
    if (activeDrawMode.value === POLYGON) {
        return $gettext(
            "Click to add vertices. Click the first point to close the polygon.",
        );
    }
    return $gettext(
        "Select a geometry type above, then click on the map to begin drawing.",
    );
});

const isSearchVisible = computed(
    () => isDrawOpen.value || drawnFeatures.value.length > 0,
);

function toggleDrawSection(): void {
    if (isDrawOpen.value) {
        setDrawMode(null);
    }
    isDrawOpen.value = !isDrawOpen.value;
}

function selectTool(tool: DrawMode): void {
    if (activeDrawMode.value === tool) {
        setDrawMode(null);
        return;
    }
    deselectDrawnFeature();
    setDrawMode(tool);
}

function applyBuffer(): void {
    setBufferForSelectedFeature(bufferDistance.value ?? 0, bufferUnits.value);
}
</script>

<template>
    <section
        class="spatial-filter-panel"
        :aria-label="$gettext('Spatial filter')"
    >
        <header class="spatial-filter-header">
            <i
                class="pi pi-map-marker spatial-filter-header-icon"
                aria-hidden="true"
            />
            <span class="spatial-filter-title">{{
                $gettext("Spatial filter")
            }}</span>
            <Button
                size="small"
                :icon="isDrawOpen ? 'pi pi-times' : 'pi pi-plus'"
                :label="isDrawOpen ? $gettext('Close') : $gettext('Add filter')"
                :severity="isDrawOpen ? undefined : 'secondary'"
                :outlined="true"
                :aria-expanded="isDrawOpen"
                @click="toggleDrawSection"
            />
        </header>
        <div class="spatial-filter-body">
            <div
                v-if="drawnFeatures.length"
                class="spatial-filter-geometries"
            >
                <span class="spatial-filter-label">{{
                    geometryCountLabel
                }}</span>
                <div class="spatial-filter-geometry-list">
                    <SpatialFilterRow
                        v-for="(feature, featureIndex) in drawnFeatures"
                        :key="String(feature.id)"
                        :feature="feature"
                        :position="featureIndex + 1"
                        :label="labelsByFeatureId[String(feature.id)]"
                        :is-selected="selectedDrawnFeature?.id === feature.id"
                        :context="resolvedContext"
                    />
                </div>
            </div>
            <template v-if="isDrawOpen">
                <div class="spatial-filter-section">
                    <span class="spatial-filter-section-title">
                        <i
                            class="pi pi-pencil"
                            aria-hidden="true"
                        />
                        <span>{{ $gettext("Draw geometry") }}</span>
                    </span>
                </div>
                <div class="spatial-filter-section">
                    <span class="spatial-filter-label">{{
                        $gettext("Geometry type")
                    }}</span>
                    <ToolButtonGroup
                        :options="geometryKindOptions"
                        :active-value="activeDrawMode"
                        @select="selectTool"
                    />
                    <div class="spatial-filter-hint">
                        <i
                            class="pi pi-info-circle"
                            aria-hidden="true"
                        />
                        <span>{{ drawHint }}</span>
                    </div>
                </div>
                <div class="spatial-filter-section">
                    <span class="spatial-filter-label">{{
                        $gettext("Buffer distance")
                    }}</span>
                    <div class="spatial-filter-buffer-row">
                        <InputNumber
                            v-model="bufferDistance"
                            class="spatial-filter-buffer-distance"
                            size="small"
                            :min="0"
                            :aria-label="$gettext('Buffer distance')"
                        />
                        <Select
                            v-model="bufferUnits"
                            class="spatial-filter-buffer-units"
                            option-label="label"
                            option-value="value"
                            size="small"
                            :options="bufferUnitOptions"
                            :aria-label="$gettext('Buffer unit')"
                        />
                    </div>
                </div>
                <div class="spatial-filter-section">
                    <div class="spatial-filter-buffer-actions">
                        <Button
                            icon="pi pi-check"
                            size="small"
                            :label="$gettext('Apply')"
                            :disabled="!selectedDrawnFeature"
                            @click="applyBuffer"
                        />
                        <Button
                            icon="pi pi-trash"
                            severity="secondary"
                            size="small"
                            :label="$gettext('Clear')"
                            :outlined="true"
                            :disabled="drawnFeatures.length === 0"
                            @click="deleteAllDrawnFeatures"
                        />
                    </div>
                </div>
            </template>
        </div>
        <div
            v-if="isSearchVisible"
            class="spatial-filter-actions"
        >
            <Button
                icon="pi pi-search"
                size="small"
                :label="$gettext('Search with this filter')"
                :disabled="drawnFeatures.length === 0"
                :fluid="true"
                @click="emit(SEARCH_EVENT)"
            />
        </div>
    </section>
</template>

<style scoped>
.spatial-filter-panel {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--p-content-background);
    color: var(--p-text-color);
    box-shadow: var(--arches-search-map-panel-shadow);
}

.spatial-filter-header {
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    gap: 0.8rem;
    padding-block: 0.8rem;
    padding-inline: 1.2rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.spatial-filter-header-icon {
    color: var(--p-primary-color);
    font-size: 1.5rem;
}

.spatial-filter-title {
    flex: 1;
    color: var(--p-primary-color);
    font-size: 1.3rem;
    font-weight: 600;
}

.spatial-filter-body {
    flex: 0 1 auto;
    min-block-size: 0;
    overflow-y: auto;
}

.spatial-filter-geometries {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding-block: 0.8rem 1rem;
    padding-inline: 1.2rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.spatial-filter-geometry-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}

.spatial-filter-section {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    padding-block: 1.4rem 1rem;
    padding-inline: 1.4rem;
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.spatial-filter-geometries:last-child,
.spatial-filter-section:last-child {
    border-block-end: none;
}

.spatial-filter-section-title {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.2rem;
    font-weight: 700;
}

.spatial-filter-section-title .pi {
    color: var(--p-primary-color);
}

.spatial-filter-label {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-weight: 600;
    letter-spacing: 0.055rem;
    text-transform: uppercase;
}

.spatial-filter-hint {
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding-block: 0.8rem;
    padding-inline: 1rem;
    border-radius: 0.6rem;
    background: var(--p-content-hover-background);
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    line-height: 1.55;
}

.spatial-filter-hint .pi {
    flex-shrink: 0;
    margin-block-start: 0.2rem;
    color: var(--p-primary-color);
    font-size: 1.2rem;
}

.spatial-filter-buffer-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.spatial-filter-buffer-distance {
    inline-size: 7.2rem;
}

.spatial-filter-buffer-units {
    flex: 1;
}

.spatial-filter-buffer-actions {
    display: flex;
    gap: 0.6rem;
}

.spatial-filter-buffer-actions .p-button {
    flex: 1;
    block-size: 3.2rem;
}

.spatial-filter-actions {
    flex: 0 0 auto;
    padding-block: 1.4rem 1rem;
    padding-inline: 1.4rem;
    border-block-start: 0.1rem solid var(--p-content-border-color);
}
</style>
