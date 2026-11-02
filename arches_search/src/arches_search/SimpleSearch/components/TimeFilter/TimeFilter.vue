<script setup lang="ts">
import { computed, ref, watch } from "vue";
import dayjs from "dayjs";
import { isEqual } from "es-toolkit";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import DatePicker from "openvue/datepicker";
import InputNumber from "openvue/inputnumber";
import Message from "openvue/message";
import Skeleton from "openvue/skeleton";

import NodeSelection from "@/arches_search/SimpleSearch/components/TimeFilter/components/NodeSelection.vue";
import TimeSlider from "@/arches_search/SimpleSearch/components/TimeFilter/components/TimeSlider.vue";
import {
    addDays,
    clamp,
    countDaysBetween,
    endOfYear,
    normalizeRange,
    parseSortableDate,
    startOfYear,
    toLocalISODateString,
} from "@/arches_search/SimpleSearch/components/TimeFilter/date-utils.ts";
import {
    buildDateSearchClause,
    buildNodeDateSearchClause,
    parseStoredDate,
} from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";
import {
    getDateBoundsForGraphId,
    getNodesForGraphId,
} from "@/arches_search/AdvancedSearch/api.ts";
import { ClauseSubjectTypeToken } from "@/arches_search/AdvancedSearch/types.ts";

import { HISTORICAL_CUTOFF_YEAR } from "@/arches_search/SimpleSearch/components/TimeFilter/constants.ts";

import type { TimeFilterNodeSummary } from "@/arches_search/SimpleSearch/components/TimeFilter/types.ts";
import type { LiteralClause } from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_MODEL_VALUE_EVENT = "update:modelValue" as const;
const REMOVE_EVENT = "remove" as const;
const CLOSE_EVENT = "close" as const;

const { graphSlug, graphId, graphLabel, modelValue } = defineProps<{
    graphSlug: string | null;
    graphId: string | null;
    graphLabel: string | null;
    modelValue: LiteralClause[];
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_MODEL_VALUE_EVENT, clauses: LiteralClause[]): void;
    (event: typeof REMOVE_EVENT): void;
    (event: typeof CLOSE_EVENT): void;
}>();

const { $gettext } = useGettext();

const selectedRange = ref<[Date, Date]>([new Date(), new Date()]);
const selectedNodeAliases = ref<string[]>(nodeAliasesFromClauses(modelValue));
const graphNodes = ref<TimeFilterNodeSummary[]>([]);
const isLoadingNodes = ref(false);
const isLoadingBounds = ref(false);
const noBoundsData = ref(false);
const hasGraphDateData = ref(true);
const isUserInitiated = ref(modelValue.length > 0);
const sliderBounds = ref<[Date, Date]>([new Date(), new Date()]);

const isLoading = computed<boolean>(
    () => isLoadingNodes.value || isLoadingBounds.value,
);

const sliderValue = computed<[number, number]>(() => {
    const startDate = sliderBounds.value[0];
    const totalDays = countDaysBetween(startDate, sliderBounds.value[1]);
    return [
        clamp(
            countDaysBetween(startDate, selectedRange.value[0]),
            0,
            totalDays,
        ),
        clamp(
            countDaysBetween(startDate, selectedRange.value[1]),
            0,
            totalDays,
        ),
    ];
});

const isSingleDay = computed<boolean>(() =>
    dayjs(sliderBounds.value[0]).isSame(sliderBounds.value[1], "day"),
);

// The slider's handles may be dragged past each other; dates read in order.
const sortedRange = computed<[Date, Date]>(() =>
    normalizeRange(selectedRange.value[0], selectedRange.value[1]),
);

const fromYear = computed<number>(() => sortedRange.value[0].getFullYear());
const toYear = computed<number>(() => sortedRange.value[1].getFullYear());
const isHistoricalFrom = computed<boolean>(
    () => fromYear.value < HISTORICAL_CUTOFF_YEAR,
);
const isHistoricalTo = computed<boolean>(
    () => toYear.value < HISTORICAL_CUTOFF_YEAR,
);

const noBoundsDataMessage = computed<string>(() => {
    if (hasGraphDateData.value) {
        return $gettext(
            "No date data found for the selected nodes. Try changing your node selection.",
        );
    }
    return $gettext("This resource type has no date data.");
});

// Only the user's own edits are emitted. Echoing a change that arrived through
// modelValue back out would re-create a filter the parent had just cleared.
// Clauses the current selection already builds, such as those edits coming
// back, have nothing to restore.
watch(
    () => modelValue,
    (clauses) => {
        if (isEqual(clauses, buildClauses())) {
            return;
        }
        isUserInitiated.value = clauses.length > 0;

        const restoredNodeAliases = nodeAliasesFromClauses(clauses);
        if (!isEqual(restoredNodeAliases, selectedNodeAliases.value)) {
            selectedNodeAliases.value = restoredNodeAliases;
        }

        const [boundsStart, boundsEnd] = sliderBounds.value;
        const firstClause = clauses[0];

        let from: Date;
        let to: Date;

        if (firstClause) {
            from =
                parseStoredDate(firstClause.operands[0]?.value) ?? boundsStart;
            to = parseStoredDate(firstClause.operands[1]?.value) ?? from;
        } else {
            from = boundsStart;
            to = boundsEnd;
        }
        const [nextFrom, nextTo] = normalizeRange(from, to);

        const unchanged =
            dayjs(nextFrom).isSame(selectedRange.value[0], "day") &&
            dayjs(nextTo).isSame(selectedRange.value[1], "day");
        if (unchanged) return;

        selectedRange.value = [nextFrom, nextTo];
    },
    { immediate: true },
);

watch(
    () => graphId,
    async (incomingGraphId, previousGraphId) => {
        if (previousGraphId) {
            selectedNodeAliases.value = [];
            isUserInitiated.value = false;
        }

        if (!incomingGraphId) {
            graphNodes.value = [];
            isLoadingNodes.value = false;
            isLoadingBounds.value = false;
            noBoundsData.value = false;
            return;
        }

        hasGraphDateData.value = true;
        isLoadingNodes.value = true;
        isLoadingBounds.value = true;

        const [nodesResult] = await Promise.allSettled([
            getNodesForGraphId(incomingGraphId),
            loadBoundsForAliases(
                incomingGraphId,
                selectedNodeAliases.value,
                Boolean(previousGraphId) || modelValue.length === 0,
            ),
        ]);

        isLoadingNodes.value = false;
        if (nodesResult.status === "fulfilled") {
            graphNodes.value = Object.values(
                nodesResult.value,
            ) as TimeFilterNodeSummary[];
        } else {
            graphNodes.value = [];
        }
    },
    { immediate: true },
);

async function loadBoundsForAliases(
    id: string,
    aliases: string[],
    resetRange: boolean,
): Promise<void> {
    isLoadingBounds.value = true;
    noBoundsData.value = false;
    try {
        const bounds = await getDateBoundsForGraphId(id, aliases);

        if (bounds.min_value === null || bounds.max_value === null) {
            noBoundsData.value = true;
            if (aliases.length === 0) hasGraphDateData.value = false;
            return;
        }

        const minDate = parseSortableDate(bounds.min_value);
        const maxDate = parseSortableDate(bounds.max_value);
        sliderBounds.value = [minDate, maxDate];
        if (resetRange) selectedRange.value = [minDate, maxDate];
    } finally {
        isLoadingBounds.value = false;
    }
}

function buildClauses(): LiteralClause[] {
    if (!graphSlug || !isUserInitiated.value) return [];

    const [rangeStart, rangeEnd] = normalizeRange(
        selectedRange.value[0],
        selectedRange.value[1],
    );
    const from = toLocalISODateString(rangeStart);
    const to = toLocalISODateString(rangeEnd);
    const nodeAliases = selectedNodeAliases.value;

    if (nodeAliases.length === 0) {
        return [buildDateSearchClause(graphSlug, "BETWEEN", from, to)];
    }
    return nodeAliases.map((alias) =>
        buildNodeDateSearchClause(graphSlug, alias, "BETWEEN", from, to),
    );
}

function nodeAliasesFromClauses(clauses: LiteralClause[]): string[] {
    return clauses
        .filter((clause) => clause.subject.type === ClauseSubjectTypeToken.NODE)
        .map((clause) => clause.subject.node_alias);
}

function emitClauses(): void {
    emit(UPDATE_MODEL_VALUE_EVENT, buildClauses());
}

function onDateFromChange(value: unknown): void {
    if (!(value instanceof Date)) return;
    isUserInitiated.value = true;
    selectedRange.value = normalizeRange(value, sortedRange.value[1]);
    emitClauses();
}

function onDateToChange(value: unknown): void {
    if (!(value instanceof Date)) return;
    isUserInitiated.value = true;
    selectedRange.value = normalizeRange(sortedRange.value[0], value);
    emitClauses();
}

function onYearFromChange(year: number | null): void {
    if (year === null) return;
    isUserInitiated.value = true;
    selectedRange.value = normalizeRange(
        startOfYear(year),
        sortedRange.value[1],
    );
    emitClauses();
}

function onYearToChange(year: number | null): void {
    if (year === null) return;
    isUserInitiated.value = true;
    selectedRange.value = normalizeRange(sortedRange.value[0], endOfYear(year));
    emitClauses();
}

function onSliderUpdate(offsets: [number, number]): void {
    isUserInitiated.value = true;
    selectedRange.value = [
        addDays(sliderBounds.value[0], offsets[0]),
        addDays(sliderBounds.value[0], offsets[1]),
    ];
    emitClauses();
}

async function onNodeSelectionUpdate(aliases: string[]): Promise<void> {
    isUserInitiated.value = true;
    selectedNodeAliases.value = aliases;
    if (graphId) await loadBoundsForAliases(graphId, aliases, true);
    emitClauses();
}
</script>

<template>
    <div class="time-filter">
        <div class="time-filter-header">
            <h3 class="time-filter-title">
                <i class="pi pi-clock" />
                {{ $gettext("Time Filter") }}
            </h3>
            <Button
                icon="pi pi-times"
                icon-pos="left"
                class="time-filter-close-btn"
                :label="$gettext('Close')"
                :text="true"
                @click="emit(CLOSE_EVENT)"
            />
        </div>

        <Transition name="loading-skeleton">
            <Skeleton
                v-if="isLoading"
                style="height: 100%"
            />
        </Transition>

        <template v-if="!isLoading">
            <section
                v-if="graphId && hasGraphDateData"
                class="time-filter-section"
            >
                <NodeSelection
                    :key="graphId"
                    :model-value="selectedNodeAliases"
                    :graph-label="graphLabel"
                    :nodes="graphNodes"
                    :loading="isLoadingNodes"
                    @update:model-value="onNodeSelectionUpdate"
                />
            </section>

            <Message
                v-if="noBoundsData"
                severity="warn"
                class="time-filter-no-data-message"
                :closable="false"
            >
                {{ noBoundsDataMessage }}
            </Message>

            <section
                v-else
                class="time-filter-section"
            >
                <h4 class="time-filter-section-heading">
                    {{ $gettext("Time Span") }}
                </h4>
                <div class="time-filter-section-body">
                    <TimeSlider
                        :model-value="sliderValue"
                        :bounds="sliderBounds"
                        :disabled="isSingleDay"
                        @update:model-value="onSliderUpdate"
                    />
                    <div class="time-filter-calendar-row">
                        <InputNumber
                            v-if="isHistoricalFrom"
                            class="time-filter-year-input"
                            :model-value="fromYear"
                            :placeholder="$gettext('From year...')"
                            :use-grouping="false"
                            :disabled="isSingleDay"
                            @update:model-value="onYearFromChange"
                        />
                        <DatePicker
                            v-else
                            class="time-filter-date-picker"
                            icon-display="input"
                            date-format="M d, yy"
                            :model-value="sortedRange[0]"
                            :placeholder="$gettext('From...')"
                            :show-icon="true"
                            :disabled="isSingleDay"
                            @update:model-value="onDateFromChange"
                        />

                        <InputNumber
                            v-if="isHistoricalTo"
                            class="time-filter-year-input"
                            :model-value="toYear"
                            :placeholder="$gettext('To year...')"
                            :use-grouping="false"
                            :disabled="isSingleDay"
                            @update:model-value="onYearToChange"
                        />
                        <DatePicker
                            v-else
                            class="time-filter-date-picker"
                            icon-display="input"
                            date-format="M d, yy"
                            :model-value="sortedRange[1]"
                            :placeholder="$gettext('To...')"
                            :show-icon="true"
                            :disabled="isSingleDay"
                            @update:model-value="onDateToChange"
                        />
                    </div>
                </div>
            </section>
        </template>
    </div>
</template>

<style scoped>
.time-filter {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    padding: 2rem;
    background-color: var(--arches-search-card-bg);
    font-size: 1rem;
    line-height: 1.45;
    height: 100%;
}

.time-filter-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-block-end: 0.75rem;
    border-block-end: 0.125rem solid var(--p-content-border-color);
}

.time-filter-title {
    margin: 0;
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--p-text-color);
}

.time-filter-title .pi {
    margin-inline-end: 0.6rem;
    color: var(--p-primary-color);
}

.time-filter-close-btn {
    padding: 0.3rem 0.8rem;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--p-text-muted-color);
    border-radius: 0.4rem;
}

.time-filter-close-btn:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.time-filter-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
}

.time-filter-section-heading {
    margin: 0;
    padding-block-end: 0.5rem;
    border-block-end: 0.125rem solid var(--p-content-border-color);
    font-weight: 600;
    font-size: 1.25rem;
    color: var(--p-text-color);
}

.time-filter-section-body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.time-filter-calendar-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
}

.time-filter-date-picker {
    flex: 1 1 13rem;
    min-width: 13rem;
    font-size: 1rem;
}

.time-filter-date-picker :deep(.p-datepicker) {
    width: 100%;
}

.time-filter-date-picker :deep(.p-inputtext) {
    font-size: 1rem;
    min-height: 3rem;
    padding: 0 1rem;
    width: 100%;
}

.time-filter-year-input {
    flex: 1 1 10rem;
    min-width: 10rem;
    font-size: 1rem;
}

.time-filter-year-input :deep(.p-inputtext) {
    font-size: 1rem;
    min-height: 3rem;
    padding: 0 1rem;
}

.time-filter-no-data-message {
    margin: 0;
}

.loading-skeleton-enter-active {
    transition: opacity 150ms ease;
    transition-delay: 200ms;
}

.loading-skeleton-enter-from {
    opacity: 0;
}
</style>
