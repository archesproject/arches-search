<script setup lang="ts">
import dayjs from "dayjs";

import { computed, onUnmounted, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import DatePicker from "primevue/datepicker";

import NodeSelection from "@/arches_search/SimpleSearch/components/TimeFilter/components/NodeSelection.vue";
import TimeSlider from "@/arches_search/SimpleSearch/components/TimeFilter/components/TimeSlider.vue";
import {
    buildDateSearchClause,
    buildNodeDateSearchClause,
    parseStoredDate,
} from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";
import { getNodesForGraphId } from "@/arches_search/AdvancedSearch/api.ts";

import type {
    LiteralClause,
    Node,
} from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_EVENT = "update:modelValue" as const;
const REMOVE_EVENT = "remove" as const;
const OPERATOR_BETWEEN = "BETWEEN" as const;
const DEFAULT_RANGE_YEARS = 1;
const EMIT_DEBOUNCE_MS = 400;
const DATE_DATATYPES = ["date", "edtf"] as const;
const SLIDER_START_DATE = "1967-04-01" as const;

const props = defineProps<{
    graphSlug: string | null;
    graphId: string | null;
    graphLabel: string | null;
    isOpen: boolean;
    modelValue: LiteralClause | null;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_EVENT, clauses: LiteralClause[]): void;
    (event: typeof REMOVE_EVENT): void;
}>();

const { $gettext } = useGettext();

const selectedRange = ref<[Date, Date]>(buildDefaultDates());
const sliderBounds = ref<[Date, Date]>(buildSliderBounds());
const sliderValue = ref<[number, number]>([
    dayjs(selectedRange.value[0]).diff(sliderBounds.value[0], "day"),
    dayjs(selectedRange.value[1]).diff(sliderBounds.value[0], "day"),
]);
const dateNodes = ref<Node[]>([]);
const selectedNodeAliases = ref<string[]>([]);
const isFilterActive = ref(false);

let emitDebounceTimer: ReturnType<typeof setTimeout> | null = null;
let lastEmittedJson = "";

const orderedRange = computed<[Date, Date]>(() =>
    normalizeRangeDates(selectedRange.value[0], selectedRange.value[1]),
);

const dateFromModel = computed<Date | null>({
    get(): Date | null {
        return orderedRange.value[0];
    },
    set(value: Date | Date[] | (Date | null)[] | null | undefined): void {
        if (value instanceof Date) {
            isFilterActive.value = true;
            setOrderedRangeDates(value, orderedRange.value[1]);
        }
    },
});

const dateToModel = computed<Date | null>({
    get(): Date | null {
        return orderedRange.value[1];
    },
    set(value: Date | Date[] | (Date | null)[] | null | undefined): void {
        if (value instanceof Date) {
            isFilterActive.value = true;
            setOrderedRangeDates(orderedRange.value[0], value);
        }
    },
});

watch(
    () => props.modelValue,
    (nextClause) => {
        isFilterActive.value = Boolean(nextClause);
        lastEmittedJson = nextClause ? JSON.stringify([nextClause]) : "";

        const [defaultFrom, defaultTo] = buildDefaultDates();
        const nextFrom = nextClause
            ? parseStoredDate(nextClause.operands[0]?.value) ?? defaultFrom
            : defaultFrom;
        const nextTo = nextClause
            ? parseStoredDate(nextClause.operands[1]?.value) ?? nextFrom
            : defaultTo;

        const start = dayjs(nextFrom).startOf("day").toDate();
        const end = dayjs(nextTo).startOf("day").toDate();
        const [currentStart, currentEnd] = orderedRange.value;

        if (
            dayjs(start).isSame(currentStart, "day") &&
            dayjs(end).isSame(currentEnd, "day")
        ) {
            return;
        }

        setOrderedRangeDates(start, end);
    },
    { immediate: true },
);

watch(
    () => props.graphId,
    async (id) => {
        selectedNodeAliases.value = [];
        if (!id) {
            dateNodes.value = [];
            return;
        }

        try {
            const nodesMap = await getNodesForGraphId(id);
            dateNodes.value = (Object.values(nodesMap) as Node[]).filter((n) =>
                (DATE_DATATYPES as readonly string[]).includes(n.datatype),
            );
        } catch {
            dateNodes.value = [];
        }
    },
    { immediate: true },
);

watch(
    () => props.isOpen,
    (isOpen) => {
        if (isOpen) {
            isFilterActive.value = true;
        }
    },
);

watch(
    [
        selectedRange,
        () => props.graphSlug,
        selectedNodeAliases,
        () => props.isOpen,
    ],
    () => {
        if (!props.graphSlug) return;
        if (!isFilterActive.value) return;

        ensureSliderBounds();
        syncSliderValue();

        const nextClauses = buildClauses();
        if (!nextClauses.length) return;

        const nextJson = JSON.stringify(nextClauses);
        if (nextJson === lastEmittedJson) return;

        if (emitDebounceTimer !== null) clearTimeout(emitDebounceTimer);
        emitDebounceTimer = setTimeout(() => {
            lastEmittedJson = nextJson;
            emit(UPDATE_EVENT, nextClauses);
            emitDebounceTimer = null;
        }, EMIT_DEBOUNCE_MS);
    },
    { immediate: true },
);

onUnmounted(() => {
    if (emitDebounceTimer !== null) clearTimeout(emitDebounceTimer);
});

function buildDefaultDates(): [Date, Date] {
    const end = dayjs().startOf("day");
    return [end.subtract(DEFAULT_RANGE_YEARS, "year").toDate(), end.toDate()];
}

function normalizeRangeDates(startDate: Date, endDate: Date): [Date, Date] {
    const start = dayjs(startDate).startOf("day");
    const end = dayjs(endDate).startOf("day");

    return start.isAfter(end)
        ? [end.toDate(), start.toDate()]
        : [start.toDate(), end.toDate()];
}

function buildSliderBounds(): [Date, Date] {
    return [
        dayjs(SLIDER_START_DATE).startOf("day").toDate(),
        dayjs().startOf("day").toDate(),
    ];
}

function ensureSliderBounds(): void {
    sliderBounds.value = buildSliderBounds();
}

function syncSliderValue(): void {
    const sliderMax = dayjs(sliderBounds.value[1]).diff(
        sliderBounds.value[0],
        "day",
    );
    sliderValue.value = [
        Math.min(
            Math.max(
                dayjs(selectedRange.value[0]).diff(
                    sliderBounds.value[0],
                    "day",
                ),
                0,
            ),
            sliderMax,
        ),
        Math.min(
            Math.max(
                dayjs(selectedRange.value[1]).diff(
                    sliderBounds.value[0],
                    "day",
                ),
                0,
            ),
            sliderMax,
        ),
    ];
}

function buildDateFromOffset(offset: number): Date {
    return dayjs(sliderBounds.value[0])
        .add(offset, "day")
        .startOf("day")
        .toDate();
}

function setOrderedRangeDates(startDate: Date, endDate: Date): void {
    selectedRange.value = normalizeRangeDates(startDate, endDate);
    ensureSliderBounds();
    syncSliderValue();
}

function formatDate(date: Date): string {
    return dayjs(date).format("YYYY-MM-DD");
}

function buildClauses(): LiteralClause[] {
    if (!props.graphSlug) return [];

    const from = formatDate(orderedRange.value[0]);
    const to = formatDate(orderedRange.value[1]);

    if (selectedNodeAliases.value.length === 0) {
        return [
            buildDateSearchClause(props.graphSlug, OPERATOR_BETWEEN, from, to),
        ];
    }

    return selectedNodeAliases.value.map((alias) =>
        buildNodeDateSearchClause(
            props.graphSlug!,
            alias,
            OPERATOR_BETWEEN,
            from,
            to,
        ),
    );
}

function onSliderUpdate(updatedValue: [number, number]): void {
    isFilterActive.value = true;
    const [startOffset, endOffset] = updatedValue;
    sliderValue.value = [startOffset, endOffset];
    selectedRange.value = [
        buildDateFromOffset(startOffset),
        buildDateFromOffset(endOffset),
    ];
    ensureSliderBounds();
    syncSliderValue();
}

function onNodeSelectionUpdate(aliases: string[]): void {
    isFilterActive.value = true;
    selectedNodeAliases.value = aliases;
}
</script>

<template>
    <div class="time-filter">
        <div
            v-if="props.graphSlug"
            class="time-filter__content"
        >
            <h3 class="time-filter__title">
                {{ $gettext("Time Filter") }}
            </h3>

            <NodeSelection
                v-if="dateNodes.length > 0"
                :model-value="selectedNodeAliases"
                :graph-label="props.graphLabel"
                :date-nodes="dateNodes"
                class="time-filter__section"
                @update:model-value="onNodeSelectionUpdate"
            />

            <section class="time-filter__section time-filter__section--range">
                <h4 class="time-filter__section-heading">
                    {{ $gettext("Time Span") }}
                </h4>

                <div class="time-filter__section-body">
                    <TimeSlider
                        :model-value="sliderValue"
                        :bounds="sliderBounds"
                        :selected-range="selectedRange"
                        @update:model-value="onSliderUpdate"
                    />

                    <div class="time-filter__calendar-row">
                        <DatePicker
                            v-model="dateFromModel"
                            class="time-filter__date-picker"
                            :placeholder="$gettext('From...')"
                            :show-icon="true"
                            icon-display="input"
                            date-format="M d, yy"
                        />

                        <DatePicker
                            v-model="dateToModel"
                            class="time-filter__date-picker"
                            :placeholder="$gettext('To...')"
                            :show-icon="true"
                            icon-display="input"
                            date-format="M d, yy"
                        />
                    </div>
                </div>
            </section>
        </div>

        <span
            v-else
            class="time-filter__empty-state"
        >
            {{ $gettext("Select a resource type to use the time filter.") }}
        </span>
    </div>
</template>

<style scoped>
.time-filter {
    --time-filter-body-size: 1.0625rem;
    --time-filter-label-size: 1.125rem;
    --time-filter-control-size: 1.0625rem;
    --time-filter-chip-size: 1.125rem;
    --time-filter-title-size: 1.5rem;
    --time-filter-section-size: 1.3125rem;
    --time-filter-heading-rule-color: var(--p-content-border-color);
    --time-filter-section-radius: 0.75rem;
    --time-filter-section-padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    padding: 2rem;
    background-color: var(--p-content-background);
    font-size: var(--time-filter-body-size);
    line-height: 1.45;
}

.time-filter__content {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.time-filter__title {
    display: block;
    inline-size: 100%;
    margin: 0;
    padding-block-end: 0.75rem;
    border-block-end: 0.125rem solid var(--time-filter-heading-rule-color);
    font-weight: 700;
    font-size: var(--time-filter-title-size);
    letter-spacing: 0.01em;
    color: var(--p-text-color);
}

.time-filter__section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: var(--time-filter-section-padding);
}

.time-filter__section--range {
    gap: 1rem;
}

.time-filter__section-heading {
    display: block;
    inline-size: 100%;
    margin: 0;
    padding-block-end: 0.5rem;
    border-block-end: 0.0625rem solid var(--time-filter-heading-rule-color);
    font-weight: 600;
    font-size: var(--time-filter-section-size);
    letter-spacing: 0.01em;
    color: var(--p-text-color);
}

.time-filter__section-body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.time-filter__calendar-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.875rem;
}

.time-filter__date-picker {
    flex: 1 1 13rem;
    min-width: 13rem;
    font-size: var(--time-filter-control-size);
}

.time-filter__date-picker :deep(.p-inputtext),
.time-filter__date-picker :deep(.p-datepicker-dropdown) {
    font-size: var(--time-filter-control-size);
}

.time-filter__date-picker :deep(.p-inputtext) {
    min-block-size: 3rem;
    padding-inline: 0.9375rem;
}

.time-filter__date-picker :deep(.p-datepicker-dropdown) {
    min-inline-size: 3rem;
}

.time-filter__empty-state {
    font-size: var(--time-filter-label-size);
    padding: var(--time-filter-section-padding);
    border: 0.0625rem solid var(--time-filter-heading-rule-color);
    border-radius: var(--time-filter-section-radius);
    color: var(--p-text-muted-color);
    line-height: 1.5;
}
</style>
