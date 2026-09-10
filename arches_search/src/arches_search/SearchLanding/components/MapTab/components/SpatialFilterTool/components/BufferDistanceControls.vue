<script setup lang="ts">
import { ref, watch } from "vue";

import { useGettext } from "vue3-gettext";

import InputNumber from "primevue/inputnumber";
import Select from "primevue/select";

import {
    FEET,
    KILOMETERS,
    METERS,
    MILES,
    YARDS,
} from "@/arches_vue_components/components/MapComponent/constants.ts";
import { useResolvedMapContext } from "@/arches_vue_components/components/MapComponent/composables/useMapContext.ts";

import type { MapContext } from "@/arches_vue_components/components/MapComponent/types.ts";

const { context = undefined } = defineProps<{
    context?: MapContext;
}>();

const { selectedDrawnFeature, setBufferForSelectedFeature } =
    useResolvedMapContext(context, "BufferDistanceControls");

const { $gettext } = useGettext();

const unitOptions = [
    { label: $gettext("Meters"), code: METERS },
    { label: $gettext("Kilometers"), code: KILOMETERS },
    { label: $gettext("Feet"), code: FEET },
    { label: $gettext("Miles"), code: MILES },
    { label: $gettext("Yards"), code: YARDS },
];

const bufferDistance = ref(0);
const selectedUnits = ref(METERS);

watch([bufferDistance, selectedUnits], () => {
    if (bufferDistance.value < 0) {
        bufferDistance.value = 0;
    }

    if (!selectedDrawnFeature.value) {
        return;
    }

    setBufferForSelectedFeature(bufferDistance.value, selectedUnits.value);
});

watch(
    selectedDrawnFeature,
    (feature) => {
        if (
            feature &&
            Number.isInteger(feature.properties?.buffer_distance) &&
            feature.properties?.buffer_units
        ) {
            bufferDistance.value = feature.properties.buffer_distance;
            selectedUnits.value = feature.properties.buffer_units;
            return;
        }

        bufferDistance.value = 0;
        selectedUnits.value = METERS;
    },
    { immediate: true },
);
</script>

<template>
    <div class="buffer-distance-controls">
        <span class="buffer-distance-controls-label">{{
            $gettext("Buffer distance")
        }}</span>
        <div class="buffer-distance-controls-row">
            <InputNumber
                v-model="bufferDistance"
                class="buffer-distance-input"
                :disabled="selectedDrawnFeature === null"
                :min="0"
            />
            <Select
                v-model="selectedUnits"
                class="buffer-distance-units"
                option-label="label"
                option-value="code"
                :disabled="selectedDrawnFeature === null"
                :options="unitOptions"
            />
        </div>
        <p
            v-if="selectedDrawnFeature === null"
            class="buffer-distance-hint"
        >
            {{ $gettext("Select a drawn shape to set a buffer around it.") }}
        </p>
    </div>
</template>

<style scoped>
.buffer-distance-controls {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.buffer-distance-controls-label {
    font-size: 1.1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05rem;
    color: var(--p-text-muted-color);
}

.buffer-distance-controls-row {
    display: flex;
    gap: 0.6rem;
    align-items: center;
}

.buffer-distance-input {
    inline-size: 9rem;
    flex-shrink: 0;
}

.buffer-distance-units {
    flex: 1;
}

.buffer-distance-hint {
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
}
</style>
