<script setup lang="ts">
import dayjs from "dayjs";

import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import DatePicker from "primevue/datepicker";
import Select from "primevue/select";

import {
    buildDateSearchClause,
    clausesMatch,
    parseStoredDate,
} from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";

import type { LiteralClause } from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_EVENT = "update:modelValue" as const;
const REMOVE_EVENT = "remove" as const;

const MODE_EQUALS = "EQUALS" as const;
const MODE_BEFORE = "BEFORE" as const;
const MODE_AFTER = "AFTER" as const;
const MODE_BETWEEN = "BETWEEN" as const;

const OPERATOR_BY_MODE: Record<string, string> = {
    [MODE_EQUALS]: "EQUALS",
    [MODE_BEFORE]: "LESS_THAN",
    [MODE_AFTER]: "GREATER_THAN",
    [MODE_BETWEEN]: "BETWEEN",
};

const OPERATOR_TO_MODE: Record<string, string> = {
    EQUALS: MODE_EQUALS,
    LESS_THAN: MODE_BEFORE,
    GREATER_THAN: MODE_AFTER,
    BETWEEN: MODE_BETWEEN,
};

type TimeFilterMode =
    | typeof MODE_EQUALS
    | typeof MODE_BEFORE
    | typeof MODE_AFTER
    | typeof MODE_BETWEEN;

const { modelValue, graphSlug } = defineProps<{
    modelValue?: LiteralClause;
    graphSlug: string;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_EVENT, clause: LiteralClause): void;
    (event: typeof REMOVE_EVENT): void;
}>();

const { $gettext } = useGettext();

const selectedMode = ref<TimeFilterMode>(MODE_EQUALS);
const dateFrom = ref<Date | null>(null);
const dateTo = ref<Date | null>(null);

const modeOptions = computed(() => [
    { label: $gettext("On"), value: MODE_EQUALS },
    { label: $gettext("Before"), value: MODE_BEFORE },
    { label: $gettext("After"), value: MODE_AFTER },
    { label: $gettext("Between"), value: MODE_BETWEEN },
]);

const isBetween = computed(() => selectedMode.value === MODE_BETWEEN);

const isValid = computed(() => {
    if (!dateFrom.value) return false;
    if (isBetween.value && !dateTo.value) return false;
    return true;
});

watch(
    () => modelValue,
    (clause) => {
        if (!clause) return;
        selectedMode.value = (OPERATOR_TO_MODE[clause.operator ?? ""] ??
            MODE_EQUALS) as TimeFilterMode;
        dateFrom.value = parseStoredDate(clause.operands[0]?.value);
        dateTo.value = parseStoredDate(clause.operands[1]?.value);
    },
    { immediate: true },
);

watch([selectedMode, dateFrom, dateTo], () => {
    if (!isValid.value || !dateFrom.value) return;
    const formatted = dayjs(dateFrom.value).format("YYYY-MM-DD");
    const formattedTo =
        isBetween.value && dateTo.value
            ? dayjs(dateTo.value).format("YYYY-MM-DD")
            : undefined;
    const nextClause = buildDateSearchClause(
        graphSlug,
        OPERATOR_BY_MODE[selectedMode.value],
        formatted,
        formattedTo,
    );
    if (clausesMatch(nextClause, modelValue)) return;
    emit(UPDATE_EVENT, nextClause);
});

function onModeChange(mode: TimeFilterMode): void {
    selectedMode.value = mode;
    dateTo.value = null;
}
</script>

<template>
    <div class="time-filter">
        <span class="time-filter__subject-label">
            {{ $gettext("Any date nodes") }}
        </span>

        <Select
            :model-value="selectedMode"
            class="time-filter__mode-select"
            :options="modeOptions"
            option-label="label"
            option-value="value"
            @update:model-value="onModeChange"
        />

        <DatePicker
            v-model="dateFrom"
            class="time-filter__date-picker"
            :placeholder="
                isBetween ? $gettext('From...') : $gettext('Select date...')
            "
            :show-icon="true"
            icon-display="input"
            date-format="yy-mm-dd"
        />

        <DatePicker
            v-if="isBetween"
            v-model="dateTo"
            class="time-filter__date-picker"
            :placeholder="$gettext('To...')"
            :min-date="dateFrom ?? undefined"
            :show-icon="true"
            icon-display="input"
            date-format="yy-mm-dd"
        />

        <Button
            class="time-filter__remove-button"
            icon="pi pi-times"
            severity="danger"
            variant="text"
            :aria-label="$gettext('Remove time filter')"
            @click="emit(REMOVE_EVENT)"
        />
    </div>
</template>

<style scoped>
.time-filter {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.time-filter__subject-label {
    white-space: nowrap;
}

.time-filter__mode-select {
    min-width: 8rem;
}

.time-filter__date-picker {
    min-width: 10rem;
}

.time-filter__remove-button {
    margin-inline-start: auto;
}
</style>
