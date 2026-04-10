<script setup lang="ts">
import dayjs from "dayjs";
import { computed } from "vue";

import Slider from "primevue/slider";

const LABEL_OVERLAP_THRESHOLD = 25;

const props = defineProps<{
    modelValue: [number, number];
    bounds: [Date, Date];
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: [number, number]): void;
}>();

const totalDays = computed<number>(() => {
    const days = dayjs(props.bounds[1]).diff(props.bounds[0], "day");
    return Math.max(days, 0);
});

const handleStartDate = computed<Date>(() =>
    dayjs(props.bounds[0]).add(props.modelValue[0], "day").toDate(),
);

const handleEndDate = computed<Date>(() =>
    dayjs(props.bounds[0]).add(props.modelValue[1], "day").toDate(),
);

const boundsStartLabel = computed<string>(() => formatDate(props.bounds[0]));
const boundsEndLabel = computed<string>(() => formatDate(props.bounds[1]));
const handleStartLabel = computed<string>(() =>
    formatDate(handleStartDate.value),
);
const handleEndLabel = computed<string>(() => formatDate(handleEndDate.value));

const handleStartPercent = computed<number>(() =>
    percentFor(props.modelValue[0], 0),
);
const handleEndPercent = computed<number>(() =>
    percentFor(props.modelValue[1], 100),
);

const labelsOverlap = computed<boolean>(() => {
    const labelDistance = Math.abs(
        handleEndPercent.value - handleStartPercent.value,
    );

    return labelDistance < LABEL_OVERLAP_THRESHOLD;
});

const combinedLabelPercent = computed<number>(
    () => (handleStartPercent.value + handleEndPercent.value) / 2,
);

const combinedLabel = computed<string>(() => {
    const startLabel = formatDate(handleStartDate.value);
    const endLabel = formatDate(handleEndDate.value);

    if (dayjs(handleStartDate.value).isSame(handleEndDate.value, "day")) {
        return startLabel;
    }

    return `${startLabel} – ${endLabel}`;
});

function formatDate(date: Date): string {
    return dayjs(date).format("MMM D, YYYY");
}

function percentFor(value: number, fallback: number): number {
    if (totalDays.value === 0) {
        return fallback;
    }

    return (value / totalDays.value) * 100;
}

function labelPosition(percent: number): Record<string, string> {
    return {
        left: `${percent}%`,
    };
}

function onSliderUpdate(value: number | number[]): void {
    if (!Array.isArray(value) || value.length < 2) {
        return;
    }

    emit("update:modelValue", [value[0], value[1]]);
}
</script>

<template>
    <div class="time-slider">
        <div class="time-slider-bounds">
            <span class="time-slider-bound">
                {{ boundsStartLabel }}
            </span>
            <span class="time-slider-bound">
                {{ boundsEndLabel }}
            </span>
        </div>

        <div class="time-slider-control">
            <div class="time-slider-terminal time-slider-terminal-start" />
            <div class="time-slider-terminal time-slider-terminal-end" />
            <Slider
                :model-value="modelValue"
                class="time-slider-input"
                :min="0"
                :max="totalDays"
                :step="1"
                :range="true"
                @update:model-value="onSliderUpdate"
            />
        </div>

        <div class="time-slider-label-track">
            <div
                v-if="labelsOverlap"
                class="time-slider-label"
                :style="labelPosition(combinedLabelPercent)"
            >
                <div class="time-slider-tick" />
                {{ combinedLabel }}
            </div>

            <template v-else>
                <div
                    class="time-slider-label"
                    :style="labelPosition(handleStartPercent)"
                >
                    <div class="time-slider-tick" />
                    {{ handleStartLabel }}
                </div>

                <div
                    class="time-slider-label"
                    :style="labelPosition(handleEndPercent)"
                >
                    <div class="time-slider-tick" />
                    {{ handleEndLabel }}
                </div>
            </template>
        </div>
    </div>
</template>

<style scoped>
.time-slider {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.time-slider-bounds {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding: 0 0.75rem;
}

.time-slider-bound,
.time-slider-label {
    color: var(--p-text-muted-color);
    font-weight: 500;
    font-size: 1rem;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    pointer-events: none;
    user-select: none;
}

.time-slider-control {
    position: relative;
    display: flex;
    align-items: center;
    min-height: 1.5rem;
    padding: 0 0.75rem;
}

.time-slider-terminal {
    position: absolute;
    top: 50%;
    width: 0.1875rem;
    height: 1.5rem;
    border-radius: 1rem;
    background-color: var(--p-content-border-color);
    transform: translateY(-50%);
    pointer-events: none;
}

.time-slider-terminal-start {
    left: 0.75rem;
}

.time-slider-terminal-end {
    right: 0.75rem;
}

.time-slider-input {
    position: relative;
    z-index: 1;
    width: 100%;
}

.time-slider-label-track {
    position: relative;
    min-height: 3.5rem;
    margin: 0 0.75rem;
}

.time-slider-label {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: center;
    transform: translateX(-50%);
}

.time-slider-tick {
    width: 0.1875rem;
    height: 0.625rem;
    margin-bottom: 0.25rem;
    border-radius: 1rem;
    background-color: var(--p-content-border-color);
}
</style>
