<script setup lang="ts">
import { computed, inject, toRef } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import InputText from "openvue/inputtext";
import Select from "openvue/select";

import PathBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/PathBuilder.vue";
import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";

import { useClauseSubjectNode } from "@/arches_search/AdvancedSearch/composables/useClauseSubjectNode.ts";
import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import {
    getClauseDatatype,
    isClauseComplete,
} from "@/arches_search/AdvancedSearch/utils/query-builder.ts";
import { ClauseSubjectTypeToken } from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    AdvancedSearchFacet,
    AdvancedSearchOperandComponent,
    LiteralClause,
    LiteralOperand,
    PathSelection,
} from "@/arches_search/AdvancedSearch/types.ts";

const CLAUSE_QUANTIFIER_ANY = "ANY" as const;
const CLAUSE_QUANTIFIER_ALL = "ALL" as const;
const CLAUSE_QUANTIFIER_NONE = "NONE" as const;

const OPERAND_TYPE_LITERAL = "LITERAL" as const;
const UPDATE_MODEL_VALUE_EVENT = "update:modelValue" as const;
const OPEN_PANEL_EVENT = "open-panel" as const;

const { modelValue, operandComponent, isEditingInPanel } = defineProps<{
    modelValue: LiteralClause;
    operandComponent: AdvancedSearchOperandComponent | null;
    isEditingInPanel: boolean;
}>();

const emit = defineEmits<{
    (
        event: typeof UPDATE_MODEL_VALUE_EVENT,
        updatedClause: LiteralClause,
    ): void;
    (event: typeof OPEN_PANEL_EVENT): void;
}>();

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();
const { subjectGraph, subjectNode } = useClauseSubjectNode(
    toRef(() => modelValue.subject),
);

const clauseQuantifierOptions = computed<
    { label: string; value: LiteralClause["quantifier"] }[]
>(() => [
    { label: $gettext("any value"), value: CLAUSE_QUANTIFIER_ANY },
    { label: $gettext("every value"), value: CLAUSE_QUANTIFIER_ALL },
]);

const isNodeSubject = computed<boolean>(
    () => modelValue.subject.type === ClauseSubjectTypeToken.NODE,
);

// A saved "every value" stays visible, so it can be changed back.
const isQuantifierShown = computed<boolean>(() => {
    if (modelValue.quantifier === CLAUSE_QUANTIFIER_ALL) {
        return true;
    }
    return (
        subjectNode.value?.nodegroup_has_cardinality_n === true &&
        modelValue.quantifier !== CLAUSE_QUANTIFIER_NONE
    );
});

const selectedSubjectNode = computed<PathSelection | null>(() => {
    if (!isNodeSubject.value || !modelValue.subject.node_alias) {
        return null;
    }
    return {
        graph_slug: modelValue.subject.graph_slug,
        node_alias: modelValue.subject.node_alias,
    };
});

const clauseDatatype = computed<string | undefined>(() =>
    getClauseDatatype(modelValue, queryBuilder.lookups),
);

const availableOperatorOptions = computed<AdvancedSearchFacet[]>(() => {
    if (!clauseDatatype.value) {
        return [];
    }
    return datatypesToAdvancedSearchFacets.value[clauseDatatype.value] ?? [];
});

const selectedAdvancedSearchFacet = computed<AdvancedSearchFacet | null>(
    () =>
        availableOperatorOptions.value.find(
            (facet) => facet.operator === modelValue.operator,
        ) ?? null,
);

const operandCount = computed<number>(
    () => selectedAdvancedSearchFacet.value?.arity ?? 0,
);

const isOperatorSetInPanel = computed<boolean>(
    () => operandComponent?.sets_operator === true,
);

const isPanelButtonShown = computed<boolean>(() => {
    if (!operandComponent) {
        return false;
    }
    return isOperatorSetInPanel.value || operandCount.value > 0;
});

const operandSummary = computed<string | null>(() => {
    const operandTexts = modelValue.operands
        .slice(0, operandCount.value)
        .map(operandText);
    if (operandTexts.some((text) => text === null)) {
        return null;
    }
    return operandTexts.join(" – ");
});

const panelButtonLabel = computed<string>(() => {
    if (!isClauseComplete(modelValue, queryBuilder.lookups)) {
        return $gettext("Set in side panel");
    }
    if (isOperatorSetInPanel.value && selectedAdvancedSearchFacet.value) {
        if (!operandSummary.value) {
            return selectedAdvancedSearchFacet.value.label;
        }
        return $gettext("%{operator} %{values}", {
            operator: selectedAdvancedSearchFacet.value.label,
            values: operandSummary.value,
        });
    }
    return operandSummary.value || $gettext("Edit in side panel");
});

function operandText(operand: LiteralOperand | undefined): string | null {
    if (!operand) {
        return null;
    }
    if (operand.display_value) {
        return operand.display_value;
    }
    if (
        typeof operand.value === "string" ||
        typeof operand.value === "number"
    ) {
        return String(operand.value);
    }
    return null;
}

function patchClause(partialClause: Partial<LiteralClause>): void {
    emit(UPDATE_MODEL_VALUE_EVENT, { ...modelValue, ...partialClause });
}

function handleSubjectUpdate(updatedSubject: PathSelection | null): void {
    patchClause({
        subject: {
            type: ClauseSubjectTypeToken.NODE,
            graph_slug:
                updatedSubject?.graph_slug ?? modelValue.subject.graph_slug,
            node_alias: updatedSubject?.node_alias ?? "",
            search_models: [],
        },
        operator: null,
        operands: [],
    });
}

function textOperandValue(parameterIndex: number): string {
    const operandValue = modelValue.operands[parameterIndex]?.value;
    if (typeof operandValue === "string") {
        return operandValue;
    }
    return "";
}

function handleTextOperandUpdate(
    parameterIndex: number,
    nextText: string | undefined,
): void {
    handleOperandUpdate(parameterIndex, {
        type: OPERAND_TYPE_LITERAL,
        value: nextText ?? "",
    });
}

function handleOperandUpdate(
    parameterIndex: number,
    updatedOperand: LiteralOperand,
): void {
    const updatedOperands = [...modelValue.operands];
    updatedOperands[parameterIndex] = updatedOperand;
    patchClause({ operands: updatedOperands });
}

function handleOperatorChange(nextOperator: string | null): void {
    if (nextOperator === modelValue.operator) {
        return;
    }
    if (nextOperator === null) {
        patchClause({ operator: null, operands: [] });
        return;
    }
    const nextFacetArity =
        availableOperatorOptions.value.find(
            (facet) => facet.operator === nextOperator,
        )?.arity ?? 0;
    if (operandCount.value !== nextFacetArity) {
        patchClause({ operator: nextOperator, operands: [] });
        return;
    }
    patchClause({ operator: nextOperator });
}

function handleQuantifierChange(
    nextQuantifier: LiteralClause["quantifier"],
): void {
    if (modelValue.quantifier === nextQuantifier) {
        return;
    }
    patchClause({ quantifier: nextQuantifier });
}
</script>

<template>
    <div class="clause-builder">
        <PathBuilder
            v-if="isNodeSubject"
            :selected-node="selectedSubjectNode"
            :graph-slugs="[modelValue.subject.graph_slug]"
            @update:selected-node="handleSubjectUpdate"
        />
        <span
            v-else
            class="clause-builder-any-field"
        >
            {{ $gettext("Any field") }}
        </span>

        <Select
            v-if="isQuantifierShown"
            option-label="label"
            option-value="value"
            :model-value="modelValue.quantifier"
            :options="clauseQuantifierOptions"
            :aria-label="$gettext('Which values must match')"
            @update:model-value="handleQuantifierChange"
        />

        <Select
            v-if="!isOperatorSetInPanel"
            option-label="label"
            option-value="operator"
            :model-value="modelValue.operator"
            :options="availableOperatorOptions"
            :disabled="availableOperatorOptions.length === 0"
            :placeholder="$gettext('Select an operator')"
            :aria-label="$gettext('Operator')"
            @update:model-value="handleOperatorChange"
        />

        <Button
            v-if="operandComponent && isPanelButtonShown"
            class="clause-builder-panel-button"
            size="small"
            severity="secondary"
            variant="outlined"
            :class="{ 'clause-builder-panel-button-editing': isEditingInPanel }"
            :icon="operandComponent.icon"
            :label="panelButtonLabel"
            @click="emit(OPEN_PANEL_EVENT)"
        />
        <template v-else-if="operandCount > 0">
            <div
                v-if="subjectNode && subjectGraph"
                class="clause-builder-operands"
            >
                <ClauseOperandBuilder
                    v-for="parameterIndex in operandCount"
                    :key="parameterIndex"
                    :model-value="
                        modelValue.operands[parameterIndex - 1] ?? null
                    "
                    :subject-terminal-node="subjectNode"
                    :subject-terminal-graph="subjectGraph"
                    @update:model-value="
                        handleOperandUpdate(parameterIndex - 1, $event)
                    "
                />
            </div>
            <div
                v-else-if="!isNodeSubject"
                class="clause-builder-operands"
            >
                <InputText
                    v-for="parameterIndex in operandCount"
                    :key="parameterIndex"
                    class="clause-builder-text"
                    :model-value="textOperandValue(parameterIndex - 1)"
                    :placeholder="$gettext('Search text')"
                    :aria-label="$gettext('Search text')"
                    @update:model-value="
                        handleTextOperandUpdate(parameterIndex - 1, $event)
                    "
                />
            </div>
        </template>
    </div>
</template>

<style scoped>
.clause-builder {
    display: contents;
    font-size: 1.2rem;
}

.clause-builder :deep(.p-select-label) {
    font-size: 1.2rem;
}

.clause-builder .clause-builder-any-field {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 600;
}

.clause-builder .clause-builder-panel-button {
    border-style: dashed;
    font-size: 1.2rem;
}

.clause-builder
    .clause-builder-panel-button.clause-builder-panel-button-editing {
    border-style: solid;
    border-color: var(--p-primary-color);
    background: var(--arches-search-primary-muted-bg);
    color: var(--p-primary-color);
    font-weight: 600;
}

.clause-builder .clause-builder-text {
    flex: 1;
    min-inline-size: 12rem;
    font-size: 1.2rem;
}

.clause-builder .clause-builder-operands {
    display: flex;
    flex: 1;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
    min-inline-size: 12rem;
}
</style>
