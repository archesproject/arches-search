<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";

import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";

import {
    isLabelList,
    referenceValuesForLabels,
} from "@/arches_search/AdvancedSearch/utils/reference-labels.ts";

import type { AliasedNodeData } from "@/arches_vue_components/types.ts";
import type { GraphModel, Node } from "@/arches_search/AdvancedSearch/types.ts";

const OPERAND_TYPE_LITERAL = "LITERAL";
const DATATYPE_REFERENCE = "reference";
const UPDATE_MODEL_VALUE = "update:modelValue" as const;

type OperandPayloadTypeToken = typeof OPERAND_TYPE_LITERAL | "PATH";

type OperandPayload = {
    type: OperandPayloadTypeToken;
    value: unknown;
    display_value?: string;
};

const { modelValue, subjectTerminalNode, subjectTerminalGraph, operandType } =
    defineProps<{
        modelValue: OperandPayload | null;
        subjectTerminalNode: Node;
        subjectTerminalGraph: GraphModel;
        operandType: OperandPayloadTypeToken;
    }>();

const emit = defineEmits<{
    (event: typeof UPDATE_MODEL_VALUE, updatedOperand: OperandPayload): void;
}>();

const operandValue = ref<unknown>(modelValue?.value ?? null);
const displayValue = ref<string | undefined>(modelValue?.display_value);
const initialValue = ref<unknown>(
    operandType === OPERAND_TYPE_LITERAL ? modelValue?.value ?? null : null,
);
const initialAliasedNodeData = ref<AliasedNodeData | undefined>(
    buildInitialAliasedNodeData(),
);
const referenceLabelLookup = labelsToLookUp();
const isLookingUpLabels = ref(referenceLabelLookup !== null);

watch(
    () => operandType,
    (updatedOperandType) => {
        handleOperandTypeChange(updatedOperandType);
        emitUpdatedOperand();
    },
);

watchEffect(async () => {
    if (!referenceLabelLookup) {
        return;
    }
    try {
        const nodeValue = await referenceValuesForLabels(
            subjectTerminalGraph.slug,
            subjectTerminalNode.alias,
            referenceLabelLookup.listId,
            referenceLabelLookup.labels,
        );
        initialAliasedNodeData.value = {
            node_value: nodeValue,
            display_value: referenceLabelLookup.labels.join(", "),
            details: [],
        };
    } catch (error) {
        console.error(error);
    } finally {
        isLookingUpLabels.value = false;
    }
});

function labelsToLookUp(): { labels: string[]; listId: string } | null {
    const value = modelValue?.value;
    if (
        operandType !== OPERAND_TYPE_LITERAL ||
        subjectTerminalNode.datatype !== DATATYPE_REFERENCE ||
        !isLabelList(value)
    ) {
        return null;
    }
    const listId = subjectTerminalNode.config.controlledList;
    if (typeof listId !== "string") {
        return null;
    }
    return { labels: value, listId };
}

function buildInitialAliasedNodeData(): AliasedNodeData | undefined {
    if (operandType !== OPERAND_TYPE_LITERAL || modelValue?.value == null) {
        return undefined;
    }
    return {
        node_value: modelValue.value,
        display_value: modelValue.display_value ?? "",
        details: [],
    };
}

function handleOperandTypeChange(
    updatedOperandType: OperandPayloadTypeToken,
): void {
    if (updatedOperandType === OPERAND_TYPE_LITERAL) {
        operandValue.value = null;
        displayValue.value = undefined;
        return;
    }

    operandValue.value = [];
    displayValue.value = undefined;
}

function emitUpdatedOperand(): void {
    emit(UPDATE_MODEL_VALUE, {
        type: operandType,
        value: operandValue.value,
        display_value: displayValue.value,
    });
}

function handleGenericWidgetUpdate(
    updatedAliasedNodeData: AliasedNodeData,
): void {
    operandValue.value = updatedAliasedNodeData.node_value;
    displayValue.value = updatedAliasedNodeData.display_value || undefined;

    emitUpdatedOperand();
}
</script>

<template>
    <div class="clause-operand-builder">
        <div class="clause-operand-editor">
            <GenericWidget
                v-if="!isLookingUpLabels"
                mode="edit"
                :graph-slug="subjectTerminalGraph.slug"
                :node-alias="subjectTerminalNode.alias"
                :should-show-label="false"
                :value="initialValue"
                :aliased-node-data="initialAliasedNodeData"
                @update:aliased-node-data="handleGenericWidgetUpdate"
            />
        </div>
    </div>
</template>

<style scoped>
.clause-operand-builder {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.clause-operand-editor {
    flex: 1 1 auto;
}
</style>
