<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import {
    DRAW_CREATE_EVENT,
    GEOMETRY_TYPE_LINESTRING,
    GEOMETRY_TYPE_POINT,
    GEOMETRY_TYPE_POLYGON,
    LINE,
    POINT,
    POLYGON,
} from "@/arches_vue_components/components/MapComponent/constants.ts";
import { useResolvedMapContext } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";

import type {
    DrawMode,
    MapContext,
} from "@/arches_vue_components/components/MapComponent/types.ts";

const { context = undefined } = defineProps<{
    context?: MapContext;
}>();

const {
    map,
    allowedGeometryTypes,
    drawnFeatures,
    selectedDrawnFeature,
    deselectDrawnFeature,
    setDrawMode,
} = useResolvedMapContext(context, "DrawTypeButtons");

const { $gettext } = useGettext();

const geometryTypeToDrawMode: Record<string, DrawMode> = {
    [GEOMETRY_TYPE_POINT]: POINT,
    [GEOMETRY_TYPE_LINESTRING]: LINE,
    [GEOMETRY_TYPE_POLYGON]: POLYGON,
};

const drawModeOptions: { mode: DrawMode; label: string; icon: string }[] = [
    { mode: POINT, label: $gettext("Point"), icon: "pi pi-map-marker" },
    { mode: LINE, label: $gettext("Line"), icon: "pi pi-minus" },
    { mode: POLYGON, label: $gettext("Polygon"), icon: "pi pi-stop" },
];

const activeDrawMode = ref<DrawMode | null>(null);
const isPickerExpanded = ref(false);

const visibleDrawModeOptions = computed(() => {
    const types = allowedGeometryTypes.value;
    if (!types?.length) {
        return drawModeOptions;
    }
    return drawModeOptions.filter((option) => types.includes(option.mode));
});

const displayedDrawMode = computed(() => {
    if (selectedDrawnFeature.value) {
        return geometryTypeToDrawMode[selectedDrawnFeature.value.geometry.type];
    }
    return activeDrawMode.value;
});

const showPicker = computed(
    () =>
        selectedDrawnFeature.value !== null ||
        isPickerExpanded.value ||
        drawnFeatures.value.length === 0,
);

const showAddButton = computed(
    () => drawnFeatures.value.length > 0 && !isPickerExpanded.value,
);

onMounted(() => {
    map.value?.on(DRAW_CREATE_EVENT, collapsePicker);
});

onUnmounted(() => {
    map.value?.off(DRAW_CREATE_EVENT, collapsePicker);
});

function collapsePicker(): void {
    activeDrawMode.value = null;
    isPickerExpanded.value = false;
}

function expandPicker(): void {
    deselectDrawnFeature();
    isPickerExpanded.value = true;
}

function onDrawModeSelected(mode: DrawMode): void {
    if (activeDrawMode.value === mode) {
        activeDrawMode.value = null;
        setDrawMode(null);
        return;
    }
    activeDrawMode.value = mode;
    setDrawMode(mode);
}
</script>

<template>
    <div class="draw-type-buttons">
        <template v-if="showPicker">
            <span class="draw-type-buttons-label">{{
                $gettext("Geometry type")
            }}</span>
            <div class="draw-type-buttons-row">
                <Button
                    v-for="option in visibleDrawModeOptions"
                    :key="option.mode"
                    class="draw-type-btn"
                    severity="secondary"
                    type="button"
                    variant="outlined"
                    :class="{ active: displayedDrawMode === option.mode }"
                    :disabled="selectedDrawnFeature !== null"
                    @click="onDrawModeSelected(option.mode)"
                >
                    <i :class="option.icon" />
                    <span>{{ option.label }}</span>
                </Button>
            </div>
        </template>
        <Button
            v-if="showAddButton"
            icon="pi pi-plus"
            icon-pos="left"
            severity="secondary"
            type="button"
            variant="outlined"
            :label="$gettext('Add geometry')"
            @click="expandPicker"
        />
    </div>
</template>

<style scoped>
.draw-type-buttons {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.draw-type-buttons-label {
    font-size: 1.1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05rem;
    color: var(--p-text-muted-color);
}

.draw-type-buttons-row {
    display: flex;
    gap: 0.6rem;
}

.draw-type-btn {
    flex: 1;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem 0.4rem;
}

.draw-type-btn.active {
    background: var(--arches-search-primary-muted-bg);
    border-color: var(--p-primary-color);
    color: var(--p-primary-color);
}
</style>
