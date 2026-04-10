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

const totalDays = computed<number>(() =>
    dayjs(props.bounds[1]).diff(props.bounds[0], "day"),
);

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
    totalDays.value > 0 ? (props.modelValue[0] / totalDays.value) * 100 : 0,
);

const handleEndPercent = computed<number>(() =>
    totalDays.value > 0 ? (props.modelValue[1] / totalDays.value) * 100 : 100,
);

const labelsOverlap = computed<boolean>(
    () =>
        Math.abs(handleEndPercent.value - handleStartPercent.value) <
        LABEL_OVERLAP_THRESHOLD,
);

const combinedLabelPercent = computed<number>(
    () => (handleStartPercent.value + handleEndPercent.value) / 2,
);

const combinedLabel = computed<string>(() => {
    if (dayjs(handleStartDate.value).isSame(handleEndDate.value, "day")) {
        return formatDate(handleStartDate.value);
    }
    return `${formatDate(handleStartDate.value)} – ${formatDate(handleEndDate.value)}`;
});

function formatDate(date: Date): string {
    return dayjs(date).format("MMM D, YYYY");
}

function onSliderUpdate(value: number | number[]): void {
    emit("update:modelValue", value as [number, number]);
}
</script>

<template>
    <div class="time-slider">
        <div class="time-slider__track">
            <span class="time-slider__bound time-slider__bound--start">
                {{ boundsStartLabel }}
            </span>
            <span class="time-slider__bound time-slider__bound--end">
                {{ boundsEndLabel }}
            </span>
            <div class="time-slider__terminal time-slider__terminal--start" />
            <div class="time-slider__terminal time-slider__terminal--end" />
            <Slider
                :model-value="modelValue"
                class="time-slider__input"
                :min="0"
                :max="totalDays"
                :step="1"
                :range="true"
                @update:model-value="onSliderUpdate"
            />
        </div>

        <div class="time-slider__handle-labels">
            <div class="time-slider__handle-label-track">
                <template v-if="labelsOverlap">
                    <div
                        class="time-slider__handle-label"
                        :style="{ '--offset': `${combinedLabelPercent}%` }"
                    >
                        <div class="time-slider__handle-tick" />
                        {{ combinedLabel }}
                    </div>
                </template>
                <template v-else>
                    <div
                        class="time-slider__handle-label"
                        :style="{ '--offset': `${handleStartPercent}%` }"
                    >
                        <div class="time-slider__handle-tick" />
                        {{ handleStartLabel }}
                    </div>
                    <div
                        class="time-slider__handle-label"
                        :style="{ '--offset': `${handleEndPercent}%` }"
                    >
                        <div class="time-slider__handle-tick" />
                        {{ handleEndLabel }}
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<style scoped>
.time-slider {
    --time-slider-inline-padding: 0.75rem;
    --time-slider-bound-gap: 2.875rem;
    --time-slider-track-size: var(--p-slider-track-size, 0.1875rem);
    --time-slider-track-color: var(--p-content-border-color);
    --time-slider-terminal-length: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.time-slider__track {
    position: relative;
    padding-block-start: var(--time-slider-bound-gap);
    padding-block-end: 0.75rem;
    padding-inline: var(--time-slider-inline-padding);
}

.time-slider__bound {
    position: absolute;
    top: 0;
    font-size: var(--time-filter-label-size, 1.0625rem);
    font-weight: 500;
    color: var(--p-text-muted-color);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    pointer-events: none;
    user-select: none;
}

.time-slider__bound--start {
    inset-inline-start: var(--time-slider-inline-padding);
}

.time-slider__bound--end {
    inset-inline-end: var(--time-slider-inline-padding);
}

.time-slider__terminal {
    position: absolute;
    inline-size: var(--time-slider-track-size);
    block-size: var(--time-slider-terminal-length);
    inset-block-start: calc(
        var(--time-slider-bound-gap) -
            (
                (
                        var(--time-slider-terminal-length) -
                            var(--time-slider-track-size)
                    ) / 2
            )
    );
    background-color: var(--time-slider-track-color);
}

.time-slider__terminal--start {
    inset-inline-start: var(--time-slider-inline-padding);
}

.time-slider__terminal--end {
    inset-inline-end: var(--time-slider-inline-padding);
}

.time-slider__input {
    inline-size: 100%;
}

.time-slider__handle-labels {
    position: relative;
    min-block-size: 3.5rem;
}

.time-slider__handle-label-track {
    position: relative;
    min-block-size: inherit;
    margin-inline: var(--time-slider-inline-padding);
}

.time-slider__handle-label {
    position: absolute;
    inset-inline-start: var(--offset);
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    font-size: var(--time-filter-label-size, 1.0625rem);
    font-weight: 500;
    color: var(--p-text-muted-color);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    pointer-events: none;
    user-select: none;
}

.time-slider__handle-tick {
    inline-size: var(--time-slider-track-size);
    block-size: 0.625rem;
    background-color: var(--time-slider-track-color);
    margin-inline: auto;
    margin-block-end: 0.25rem;
    border-radius: 999px;
}
</style>
