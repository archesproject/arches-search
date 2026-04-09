<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import InputText from "primevue/inputtext";

import type {
    AdvancedSearchFacet,
    LiteralClause,
    LiteralOperand,
} from "@/arches_search/AdvancedSearch/types.ts";

const OPERAND_TYPE_LITERAL = "LITERAL" as const;

const { modelValue, availableOperatorOptions } = defineProps<{
    modelValue: LiteralClause;
    availableOperatorOptions: AdvancedSearchFacet[];
}>();

const emit = defineEmits<{
    (event: "update:modelValue", updatedClause: LiteralClause): void;
}>();

const { $gettext } = useGettext();

const selectedAdvancedSearchFacet = computed<AdvancedSearchFacet | null>(() => {
    if (!modelValue.operator) {
        return null;
    }

    const matchingFacet = availableOperatorOptions.find((searchFacet) => {
        return searchFacet.operator === modelValue.operator;
    });

    return matchingFacet ?? null;
});

function patchClause(partialClause: Partial<LiteralClause>): void {
    emit("update:modelValue", { ...modelValue, ...partialClause });
}

function handleOperatorChange(nextOperator: string | null): void {
    if (nextOperator === modelValue.operator) {
        return;
    }

    if (nextOperator === null) {
        patchClause({ operator: null, operands: [] });
        return;
    }

    const previousFacetArity = selectedAdvancedSearchFacet.value?.arity ?? 0;
    const nextSearchFacet = availableOperatorOptions.find((searchFacet) => {
        return searchFacet.operator === nextOperator;
    });
    const nextFacetArity = nextSearchFacet?.arity ?? 0;

    if (previousFacetArity !== nextFacetArity) {
        patchClause({ operator: nextOperator, operands: [] });
        return;
    }

    patchClause({ operator: nextOperator });
}

function handleOperandUpdate(
    parameterIndex: number,
    updatedValue: LiteralOperand["value"],
): void {
    const updatedOperands = [...modelValue.operands];
    updatedOperands[parameterIndex] = {
        type: OPERAND_TYPE_LITERAL,
        value: updatedValue,
    };

    patchClause({ operands: updatedOperands });
}
</script>

<template>
    <span class="text-search-filter__subject-label">
        {{ $gettext("Any text nodes") }}
    </span>

    <Select
        :model-value="modelValue.operator"
        class="text-search-filter__operator-select"
        :options="availableOperatorOptions"
        option-label="label"
        option-value="operator"
        :disabled="availableOperatorOptions.length === 0"
        :placeholder="$gettext('Select an operator...')"
        @update:model-value="handleOperatorChange"
    />

    <div
        v-if="
            selectedAdvancedSearchFacet && selectedAdvancedSearchFacet.arity > 0
        "
        class="text-search-filter__operands-row"
    >
        <InputText
            v-for="parameterIndex in selectedAdvancedSearchFacet.arity"
            :key="parameterIndex"
            :model-value="
                (modelValue.operands[parameterIndex - 1]?.value as string) ?? ''
            "
            :placeholder="$gettext('Search text...')"
            @update:model-value="
                handleOperandUpdate(parameterIndex - 1, $event as string)
            "
        />
    </div>
</template>

<style scoped>
.text-search-filter__subject-label {
    white-space: nowrap;
}

.text-search-filter__operands-row {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    flex-wrap: wrap;
}
</style>
