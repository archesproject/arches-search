<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";

import GenericWidget from "@/arches_component_lab/generics/GenericWidget/GenericWidget.vue";

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

const operandValue = ref<unknown>(null);
const displayValue = ref<string | undefined>(undefined);
const initialAliasedNodeData = ref<Record<string, unknown> | null>(null);
const hasInitializedFromModel = ref(false);

watchEffect(() => {
    if (hasInitializedFromModel.value) {
        return;
    }

    if (modelValue === null || modelValue.value === undefined) {
        operandValue.value = null;
        displayValue.value = undefined;
        initialAliasedNodeData.value = null;
        hasInitializedFromModel.value = true;
        return;
    }

    operandValue.value = modelValue.value;
    displayValue.value = modelValue.display_value;

    if (operandType === OPERAND_TYPE_LITERAL) {
        initialAliasedNodeData.value = modelValue.value as Record<
            string,
            unknown
        >;
    } else {
        initialAliasedNodeData.value = null;
    }

    hasInitializedFromModel.value = true;
});

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

        if (modelValue !== null && modelValue.value !== undefined) {
            initialAliasedNodeData.value = modelValue.value as Record<
                string,
                unknown
            >;
        } else {
            initialAliasedNodeData.value = null;
        }

        return;
    }

    operandValue.value = [];
    displayValue.value = undefined;
    initialAliasedNodeData.value = null;
}

function emitUpdatedOperand(): void {
    emit("update:modelValue", {
        type: operandType,
        value: operandValue.value,
        display_value: displayValue.value,
    });
}

function handleGenericWidgetUpdate(
    updatedWidgetValue: Record<string, unknown>,
): void {
    if (
        "node_value" in updatedWidgetValue &&
        "display_value" in updatedWidgetValue
    ) {
        operandValue.value = updatedWidgetValue.node_value;

        const rawDisplayValue = String(
            updatedWidgetValue.display_value ?? "",
        ).trim();

        displayValue.value = rawDisplayValue || undefined;
    } else {
        operandValue.value = updatedWidgetValue;
        displayValue.value = undefined;
    }

    emitUpdatedOperand();
}
</script>

<template>
    <div class="clause-operand-builder">
        <GenericWidget
            class="clause-operand-editor"
            mode="edit"
            :graph-slug="subjectTerminalGraph.slug"
            :node-alias="subjectTerminalNode.alias"
            :should-show-label="false"
            :aliased-node-data="initialAliasedNodeData || undefined"
            :should-emit-simplified-value="true"
            @update:value="handleGenericWidgetUpdate"
        />
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
