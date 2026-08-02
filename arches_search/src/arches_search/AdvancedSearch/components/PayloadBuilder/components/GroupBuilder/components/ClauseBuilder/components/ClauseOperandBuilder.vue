<script setup lang="ts">
import { ref, watch } from "vue";

import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";

import type { GraphModel, Node } from "@/arches_search/AdvancedSearch/types.ts";

const OPERAND_TYPE_LITERAL = "LITERAL";

type OperandPayloadTypeToken = typeof OPERAND_TYPE_LITERAL | "PATH";

type OperandPayload = {
    type: OperandPayloadTypeToken;
    value: unknown;
    display_value?: string;
};

const emit = defineEmits<{
    "update:modelValue": [updatedOperand: OperandPayload];
}>();

const { modelValue, subjectTerminalNode, subjectTerminalGraph, operandType } =
    defineProps<{
        modelValue: OperandPayload | null;
        subjectTerminalNode: Node;
        subjectTerminalGraph: GraphModel;
        operandType: OperandPayloadTypeToken;
    }>();

const operandValue = ref<unknown>(modelValue?.value ?? null);
const displayValue = ref<string | undefined>(modelValue?.display_value);
const initialValue = ref<unknown>(
    operandType === OPERAND_TYPE_LITERAL ? modelValue?.value ?? null : null,
);

watch(
    () => operandType,
    (updatedOperandType) => {
        handleOperandTypeChange(updatedOperandType);
        emitUpdatedOperand();
    },
);

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
    emit("update:modelValue", {
        type: operandType,
        value: operandValue.value,
        display_value: displayValue.value,
    });
}

function handleGenericWidgetUpdate(updatedWidgetValue: unknown): void {
    operandValue.value = updatedWidgetValue;
    displayValue.value = undefined;

    emitUpdatedOperand();
}
</script>

<template>
    <div class="clause-operand-builder">
        <div class="clause-operand-editor">
            <GenericWidget
                mode="edit"
                :graph-slug="subjectTerminalGraph.slug"
                :node-alias="subjectTerminalNode.alias"
                :should-show-label="false"
                :value="initialValue"
                @update:value="handleGenericWidgetUpdate"
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
