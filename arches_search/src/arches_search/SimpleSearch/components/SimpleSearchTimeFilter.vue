<script setup lang="ts">
import dayjs from "dayjs";

import { computed, onUnmounted, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import DatePicker from "primevue/datepicker";
import Slider from "primevue/slider";

import {
    buildDateSearchClause,
    clausesMatch,
    parseStoredDate,
} from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";

import type { LiteralClause } from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_EVENT = "update:modelValue" as const;
const REMOVE_EVENT = "remove" as const;
const OPERATOR_BETWEEN = "BETWEEN" as const;
const DEFAULT_RANGE_YEARS = 1;
const RANGE_PADDING_YEARS = 10;
const EMIT_DEBOUNCE_MS = 400;

const props = defineProps<{
    graphSlug: string | null;
    modelValue: LiteralClause | null;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_EVENT, clause: LiteralClause): void;
    (event: typeof REMOVE_EVENT): void;
}>();

const { $gettext } = useGettext();

const selectedRange = ref<[Date, Date]>(buildDefaultDates());
const sliderBounds = ref<[Date, Date]>(
    buildSliderBounds(...selectedRange.value),
);
const sliderValue = ref<[number, number]>([
    dayjs(selectedRange.value[0]).diff(sliderBounds.value[0], "day"),
    dayjs(selectedRange.value[1]).diff(sliderBounds.value[0], "day"),
]);

let emitDebounceTimer: ReturnType<typeof setTimeout> | null = null;

const sliderMax = computed<number>(() => {
    return dayjs(sliderBounds.value[1]).diff(sliderBounds.value[0], "day");
});

const sliderMinLabel = computed<string>(() =>
    formatDate(selectedRange.value[0]),
);
const sliderMaxLabel = computed<string>(() =>
    formatDate(selectedRange.value[1]),
);

const dateFromModel = computed<Date | null>({
    get(): Date | null {
        return selectedRange.value[0];
    },
    set(value: Date | Date[] | (Date | null)[] | null | undefined): void {
        if (value instanceof Date) setStartDate(value);
    },
});

const dateToModel = computed<Date | null>({
    get(): Date | null {
        return selectedRange.value[1];
    },
    set(value: Date | Date[] | (Date | null)[] | null | undefined): void {
        if (value instanceof Date) setEndDate(value);
    },
});

watch(
    () => props.modelValue,
    (nextClause) => {
        const [defaultFrom, defaultTo] = buildDefaultDates();
        const nextFrom = nextClause
            ? parseStoredDate(nextClause.operands[0]?.value) ?? defaultFrom
            : defaultFrom;
        const nextTo = nextClause
            ? parseStoredDate(nextClause.operands[1]?.value) ?? nextFrom
            : defaultTo;

        const start = dayjs(nextFrom).startOf("day").toDate();
        const end = dayjs(nextTo).startOf("day").toDate();

        if (
            dayjs(start).isSame(selectedRange.value[0], "day") &&
            dayjs(end).isSame(selectedRange.value[1], "day")
        ) {
            return;
        }

        selectedRange.value = [start, end];
        sliderBounds.value = buildSliderBounds(start, end);
        syncSliderValue();
    },
    { immediate: true },
);

watch([selectedRange, () => props.graphSlug], () => {
    if (!props.graphSlug) return;

    ensureSliderBounds(...selectedRange.value);

    const nextClause = buildClause();
    if (!nextClause || clausesMatch(nextClause, props.modelValue)) return;

    if (emitDebounceTimer !== null) clearTimeout(emitDebounceTimer);
    emitDebounceTimer = setTimeout(() => {
        emit(UPDATE_EVENT, nextClause);
        emitDebounceTimer = null;
    }, EMIT_DEBOUNCE_MS);
});

onUnmounted(() => {
    if (emitDebounceTimer !== null) clearTimeout(emitDebounceTimer);
});

function buildDefaultDates(): [Date, Date] {
    const end = dayjs().startOf("day");
    return [end.subtract(DEFAULT_RANGE_YEARS, "year").toDate(), end.toDate()];
}

function buildSliderBounds(startDate: Date, endDate: Date): [Date, Date] {
    const a = dayjs(startDate);
    const b = dayjs(endDate);
    return [
        (a.isBefore(b) ? a : b)
            .startOf("year")
            .subtract(RANGE_PADDING_YEARS, "year")
            .toDate(),
        (a.isAfter(b) ? a : b)
            .endOf("year")
            .add(RANGE_PADDING_YEARS, "year")
            .toDate(),
    ];
}

function ensureSliderBounds(startDate: Date, endDate: Date): void {
    let [lower, upper] = sliderBounds.value.map((d) => dayjs(d));
    if (dayjs(startDate).isBefore(lower, "day")) {
        lower = dayjs(startDate)
            .startOf("year")
            .subtract(RANGE_PADDING_YEARS, "year");
    }
    if (dayjs(endDate).isAfter(upper, "day")) {
        upper = dayjs(endDate).endOf("year").add(RANGE_PADDING_YEARS, "year");
    }
    sliderBounds.value = [lower.toDate(), upper.toDate()];
}

function syncSliderValue(): void {
    sliderValue.value = [
        dayjs(selectedRange.value[0]).diff(sliderBounds.value[0], "day"),
        dayjs(selectedRange.value[1]).diff(sliderBounds.value[0], "day"),
    ];
}

function setRangeDates(startDate: Date, endDate: Date): void {
    selectedRange.value = [
        dayjs(startDate).startOf("day").toDate(),
        dayjs(endDate).startOf("day").toDate(),
    ];
    ensureSliderBounds(...selectedRange.value);
    syncSliderValue();
}

function setStartDate(startDate: Date): void {
    const start = dayjs(startDate).startOf("day");
    const end = dayjs(selectedRange.value[1]).startOf("day");
    setRangeDates((start.isAfter(end) ? end : start).toDate(), end.toDate());
}

function setEndDate(endDate: Date): void {
    const start = dayjs(selectedRange.value[0]).startOf("day");
    const end = dayjs(endDate).startOf("day");
    setRangeDates(start.toDate(), (end.isBefore(start) ? start : end).toDate());
}

function formatDate(date: Date): string {
    return dayjs(date).format("YYYY-MM-DD");
}

function buildClause(): LiteralClause | null {
    if (!props.graphSlug) return null;
    return buildDateSearchClause(
        props.graphSlug,
        OPERATOR_BETWEEN,
        formatDate(selectedRange.value[0]),
        formatDate(selectedRange.value[1]),
    );
}

function onSliderUpdate(updatedValue: number | number[]): void {
    const [startOffset, endOffset] = updatedValue as [number, number];
    sliderValue.value = [startOffset, endOffset];
    selectedRange.value = [
        dayjs(sliderBounds.value[0])
            .add(startOffset, "day")
            .startOf("day")
            .toDate(),
        dayjs(sliderBounds.value[0])
            .add(endOffset, "day")
            .startOf("day")
            .toDate(),
    ];
    ensureSliderBounds(...selectedRange.value);
}
</script>

<template>
    <div class="simple-search-time-filter">
        <div
            v-if="props.graphSlug"
            class="simple-search-time-filter__content"
        >
            <div class="simple-search-time-filter__header">
                <span class="simple-search-time-filter__subject-label">
                    {{ $gettext("Any date nodes") }}
                </span>

                <Button
                    class="simple-search-time-filter__remove-button"
                    icon="pi pi-times"
                    severity="danger"
                    variant="text"
                    :aria-label="$gettext('Remove time filter')"
                    @click="emit(REMOVE_EVENT)"
                />
            </div>

            <div class="simple-search-time-filter__slider-row">
                <span class="simple-search-time-filter__slider-label">
                    {{ sliderMinLabel }}
                </span>

                <Slider
                    :model-value="sliderValue"
                    class="simple-search-time-filter__slider"
                    :min="0"
                    :max="sliderMax"
                    :step="1"
                    :range="true"
                    @update:model-value="onSliderUpdate"
                />

                <span class="simple-search-time-filter__slider-label">
                    {{ sliderMaxLabel }}
                </span>
            </div>

            <div class="simple-search-time-filter__calendar-row">
                <DatePicker
                    v-model="dateFromModel"
                    class="simple-search-time-filter__date-picker"
                    :placeholder="$gettext('From...')"
                    :show-icon="true"
                    icon-display="input"
                    date-format="yy-mm-dd"
                />

                <DatePicker
                    v-model="dateToModel"
                    class="simple-search-time-filter__date-picker"
                    :placeholder="$gettext('To...')"
                    :min-date="dateFromModel ?? undefined"
                    :show-icon="true"
                    icon-display="input"
                    date-format="yy-mm-dd"
                />
            </div>
        </div>

        <span
            v-else
            class="simple-search-time-filter__empty-state"
        >
            {{ $gettext("Select a resource type to use the time filter.") }}
        </span>
    </div>
</template>

<style scoped>
.simple-search-time-filter {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-block-end: 0.0625rem solid var(--p-content-border-color);
    background-color: var(--p-content-background);
}

.simple-search-time-filter__content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.simple-search-time-filter__header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.simple-search-time-filter__subject-label {
    white-space: nowrap;
}

.simple-search-time-filter__remove-button {
    margin-inline-start: auto;
}

.simple-search-time-filter__slider-row {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 0.75rem;
}

.simple-search-time-filter__slider {
    inline-size: 100%;
}

.simple-search-time-filter__slider-label {
    color: var(--p-text-muted-color);
    white-space: nowrap;
}

.simple-search-time-filter__calendar-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.simple-search-time-filter__date-picker {
    min-width: 10rem;
}

.simple-search-time-filter__empty-state {
    color: var(--p-text-muted-color);
}
</style>
