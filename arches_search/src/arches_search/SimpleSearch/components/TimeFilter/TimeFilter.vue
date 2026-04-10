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

import type { TimeFilterNodeSummary } from "@/arches_search/SimpleSearch/components/TimeFilter/types.ts";
import type { LiteralClause } from "@/arches_search/AdvancedSearch/types.ts";

const EMIT_DEBOUNCE_MS = 400;
const SLIDER_START_DATE = "1967-04-01";

const { graphSlug, graphId, graphLabel, isOpen, modelValue } = defineProps<{
    graphSlug: string | null;
    graphId: string | null;
    graphLabel: string | null;
    isOpen: boolean;
    modelValue: LiteralClause | null;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", clauses: LiteralClause[]): void;
    (event: "remove"): void;
}>();

const { $gettext } = useGettext();

const selectedRange = ref<[Date, Date]>(defaultRange());
const selectedNodeAliases = ref<string[]>([]);
const graphNodes = ref<TimeFilterNodeSummary[]>([]);
const isLoadingNodes = ref(false);
const isFilterActive = ref(false);

let emitTimer: ReturnType<typeof setTimeout> | null = null;
let lastEmittedJson = "";
let nodeLoadId = 0;

const sliderBounds = computed<[Date, Date]>(() => [
    dayjs(SLIDER_START_DATE).startOf("day").toDate(),
    dayjs().startOf("day").toDate(),
]);

const sliderValue = computed<[number, number]>(() => {
    const start = sliderBounds.value[0];
    const total = dayjs(sliderBounds.value[1]).diff(start, "day");
    return [
        clamp(dayjs(selectedRange.value[0]).diff(start, "day"), 0, total),
        clamp(dayjs(selectedRange.value[1]).diff(start, "day"), 0, total),
    ];
});

watch(
    () => modelValue,
    (clause) => {
        isFilterActive.value = Boolean(clause);
        lastEmittedJson = "";

        if (clause) {
            lastEmittedJson = JSON.stringify([clause]);
        }

        const [defaultFrom, defaultTo] = defaultRange();
        let from = defaultFrom;
        let to = defaultTo;

        if (clause) {
            from = parseStoredDate(clause.operands[0]?.value) ?? defaultFrom;
            to = parseStoredDate(clause.operands[1]?.value) ?? from;
        }

        const next = normalizeRange(
            dayjs(from).startOf("day").toDate(),
            dayjs(to).startOf("day").toDate(),
        );

        if (
            dayjs(next[0]).isSame(selectedRange.value[0], "day") &&
            dayjs(next[1]).isSame(selectedRange.value[1], "day")
        ) {
            return;
        }

        selectedRange.value = next;
    },
    { immediate: true },
);

watch(
    () => graphId,
    async (id) => {
        const thisLoad = ++nodeLoadId;
        selectedNodeAliases.value = [];

        if (!id) {
            graphNodes.value = [];
            isLoadingNodes.value = false;
            return;
        }

        isLoadingNodes.value = true;
        try {
            const nodesMap = await getNodesForGraphId(id);
            if (thisLoad !== nodeLoadId) return;
            graphNodes.value = Object.values(
                nodesMap,
            ) as TimeFilterNodeSummary[];
        } catch {
            if (thisLoad !== nodeLoadId) return;
            graphNodes.value = [];
        } finally {
            if (thisLoad === nodeLoadId) isLoadingNodes.value = false;
        }
    },
    { immediate: true },
);

watch(
    () => isOpen,
    (isOpen) => {
        if (isOpen) isFilterActive.value = true;
    },
);

watch(
    [selectedRange, () => graphSlug, selectedNodeAliases, () => isOpen],
    () => {
        if (!graphSlug || !isFilterActive.value) return;

        const nextClauses = buildClauses();
        if (!nextClauses.length) return;

        const nextJson = JSON.stringify(nextClauses);
        if (nextJson === lastEmittedJson) return;

        if (emitTimer !== null) clearTimeout(emitTimer);
        emitTimer = setTimeout(() => {
            lastEmittedJson = nextJson;
            emit("update:modelValue", nextClauses);
            emitTimer = null;
        }, EMIT_DEBOUNCE_MS);
    },
    { immediate: true },
);

onUnmounted(() => {
    if (emitTimer !== null) clearTimeout(emitTimer);
});

function clamp(value: number, min: number, max: number): number {
    return Math.min(Math.max(value, min), max);
}

function normalizeRange(a: Date, b: Date): [Date, Date] {
    const start = dayjs(a).startOf("day");
    const end = dayjs(b).startOf("day");

    if (start.isAfter(end)) {
        return [end.toDate(), start.toDate()];
    }

    return [start.toDate(), end.toDate()];
}

function defaultRange(): [Date, Date] {
    const boundsStart = dayjs(SLIDER_START_DATE).startOf("day");
    const total = dayjs().startOf("day").diff(boundsStart, "day");
    return [
        boundsStart.add(Math.floor(total / 3), "day").toDate(),
        boundsStart.add(Math.ceil((total * 2) / 3), "day").toDate(),
    ];
}

function buildClauses(): LiteralClause[] {
    const slug = graphSlug;
    if (!slug) return [];

    const from = dayjs(selectedRange.value[0]).format("YYYY-MM-DD");
    const to = dayjs(selectedRange.value[1]).format("YYYY-MM-DD");

    if (selectedNodeAliases.value.length === 0) {
        return [buildDateSearchClause(slug, "BETWEEN", from, to)];
    }

    return selectedNodeAliases.value.map((alias) =>
        buildNodeDateSearchClause(slug, alias, "BETWEEN", from, to),
    );
}

function onDateFromChange(value: unknown): void {
    if (!(value instanceof Date)) return;
    isFilterActive.value = true;
    selectedRange.value = normalizeRange(value, selectedRange.value[1]);
}

function onDateToChange(value: unknown): void {
    if (!(value instanceof Date)) return;
    isFilterActive.value = true;
    selectedRange.value = normalizeRange(selectedRange.value[0], value);
}

function onSliderUpdate(offsets: [number, number]): void {
    isFilterActive.value = true;
    selectedRange.value = [
        dayjs(sliderBounds.value[0])
            .add(offsets[0], "day")
            .startOf("day")
            .toDate(),
        dayjs(sliderBounds.value[0])
            .add(offsets[1], "day")
            .startOf("day")
            .toDate(),
    ];
}

function onNodeSelectionUpdate(aliases: string[]): void {
    isFilterActive.value = true;
    selectedNodeAliases.value = aliases;
}
</script>

<template>
    <div class="time-filter">
        <div
            v-if="graphSlug"
            class="time-filter-content"
        >
            <h3 class="time-filter-title">
                {{ $gettext("Time Filter") }}
            </h3>

            <NodeSelection
                v-if="graphId"
                :key="graphId"
                :model-value="selectedNodeAliases"
                :graph-label="graphLabel"
                :nodes="graphNodes"
                :loading="isLoadingNodes"
                class="time-filter-section"
                @update:model-value="onNodeSelectionUpdate"
            />

            <section class="time-filter-section">
                <h4 class="time-filter-section-heading">
                    {{ $gettext("Time Span") }}
                </h4>

                <div class="time-filter-section-body">
                    <TimeSlider
                        :model-value="sliderValue"
                        :bounds="sliderBounds"
                        @update:model-value="onSliderUpdate"
                    />

                    <div class="time-filter-calendar-row">
                        <DatePicker
                            :model-value="selectedRange[0]"
                            class="time-filter-date-picker"
                            :placeholder="$gettext('From...')"
                            :show-icon="true"
                            icon-display="input"
                            date-format="M d, yy"
                            @update:model-value="onDateFromChange"
                        />

                        <DatePicker
                            :model-value="selectedRange[1]"
                            class="time-filter-date-picker"
                            :placeholder="$gettext('To...')"
                            :show-icon="true"
                            icon-display="input"
                            date-format="M d, yy"
                            @update:model-value="onDateToChange"
                        />
                    </div>
                </div>
            </section>
        </div>

        <span
            v-else
            class="time-filter-empty-state"
        >
            {{ $gettext("Select a resource type to use the time filter.") }}
        </span>
    </div>
</template>

<style scoped>
.time-filter {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    padding: 2rem;
    background-color: var(--p-content-background);
    font-size: 1rem;
    line-height: 1.45;
}

.time-filter-content {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.time-filter-title {
    margin: 0;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--p-content-border-color);
    font-weight: 700;
    font-size: 1.5rem;
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
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--p-content-border-color);
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

.time-filter-date-picker :deep(.p-inputtext),
.time-filter-date-picker :deep(.p-datepicker-dropdown) {
    font-size: 1rem;
}

.time-filter-date-picker :deep(.p-inputtext) {
    min-height: 3rem;
    padding: 0 1rem;
}

.time-filter-date-picker :deep(.p-datepicker-dropdown) {
    min-width: 3rem;
}

.time-filter-empty-state {
    padding: 1rem;
    border: 1px solid var(--p-content-border-color);
    border-radius: 0.5rem;
    font-size: 1rem;
    color: var(--p-text-muted-color);
    line-height: 1.5;
}
</style>
