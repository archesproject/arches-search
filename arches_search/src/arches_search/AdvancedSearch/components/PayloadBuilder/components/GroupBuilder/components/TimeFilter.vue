<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import dayjs from "dayjs";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import DatePicker from "primevue/datepicker";
import Select from "primevue/select";

import {
    buildDateSearchClause,
    clausesMatch,
    parseStoredDate,
} from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";

import type { Ref } from "vue";
import type {
    AdvancedSearchFacet,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_EVENT = "update:modelValue" as const;
const REMOVE_EVENT = "remove" as const;

const { modelValue, graphSlug } = defineProps<{
    modelValue?: LiteralClause;
    graphSlug: string;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_EVENT, clause: LiteralClause): void;
    (event: typeof REMOVE_EVENT): void;
}>();

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;

const { $gettext } = useGettext();

const selectedFacet = ref<AdvancedSearchFacet | null>(null);
const dateFrom = ref<Date | null>(null);
const dateTo = ref<Date | null>(null);

const dateFilterFacets = computed<AdvancedSearchFacet[]>(() =>
    (datatypesToAdvancedSearchFacets.value["date"] ?? []).filter(
        (facet) => facet.arity > 0,
    ),
);

const isBetween = computed(() => selectedFacet.value?.arity === 2);

const isValid = computed(() => {
    if (!selectedFacet.value || !dateFrom.value) return false;
    if (isBetween.value && !dateTo.value) return false;
    return true;
});

watch(
    [() => modelValue, dateFilterFacets],
    ([clause]) => {
        if (!clause) return;
        selectedFacet.value =
            dateFilterFacets.value.find(
                (facet) => facet.operator === clause.operator,
            ) ?? null;
        dateFrom.value = parseStoredDate(clause.operands[0]?.value);
        dateTo.value = parseStoredDate(clause.operands[1]?.value);
    },
    { immediate: true },
);

watch([selectedFacet, dateFrom, dateTo], () => {
    if (!isValid.value) return;
    const from = dayjs(dateFrom.value!).format("YYYY-MM-DD");
    const to =
        isBetween.value && dateTo.value
            ? dayjs(dateTo.value).format("YYYY-MM-DD")
            : undefined;
    const nextClause = buildDateSearchClause(
        graphSlug,
        selectedFacet.value!.operator,
        from,
        to,
    );
    if (clausesMatch(nextClause, modelValue)) return;
    emit(UPDATE_EVENT, nextClause);
});

function onFacetChange(facet: AdvancedSearchFacet): void {
    if (selectedFacet.value?.arity === 2 && facet.arity !== 2) {
        dateTo.value = null;
    }
    selectedFacet.value = facet;
}
</script>

<template>
    <div class="time-filter">
        <span class="time-filter-subject-label">
            {{ $gettext("Any date nodes") }}
        </span>

        <Select
            :model-value="selectedFacet"
            class="time-filter-facet-select"
            :options="dateFilterFacets"
            option-label="label"
            @update:model-value="onFacetChange"
        />

        <DatePicker
            v-model="dateFrom"
            class="time-filter-date-picker"
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
            class="time-filter-date-picker"
            :placeholder="$gettext('To...')"
            :min-date="dateFrom ?? undefined"
            :show-icon="true"
            icon-display="input"
            date-format="yy-mm-dd"
        />

        <Button
            class="time-filter-remove-button"
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

.time-filter-subject-label {
    white-space: nowrap;
}

.time-filter-facet-select {
    min-width: 8rem;
}

.time-filter-date-picker {
    min-width: 10rem;
}

.time-filter-remove-button {
    margin-inline-start: auto;
}
</style>
