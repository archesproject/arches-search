<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";

import GenericWidget from "@/arches_component_lab/generics/GenericWidget/GenericWidget.vue";

import type { GraphModel, Node } from "@/arches_search/AdvancedSearch/types.ts";

const OPERAND_TYPE_LITERAL = "LITERAL";

type OperandPayloadTypeToken = typeof OPERAND_TYPE_LITERAL | "PATH";

type OperandPayload = {
    type: OperandPayloadTypeToken;
    value: unknown;
};

const emit = defineEmits<{
    (event: "update:modelValue", updatedOperand: OperandPayload): void;
}>();

const { modelValue, subjectTerminalNode, subjectTerminalGraph, operandType } =
    defineProps<{
        modelValue: OperandPayload | null;
        subjectTerminalNode: Node;
        subjectTerminalGraph: GraphModel;
        operandType: OperandPayloadTypeToken;
    }>();

const operandValue = ref<unknown>(null);
const initialAliasedNodeData = ref<Record<string, unknown> | null>(null);
const hasInitializedFromModel = ref(false);

watchEffect(() => {
    if (hasInitializedFromModel.value) {
        return;
    }

    const hasInitialValue = hasInitialOperandValue();

    if (hasInitialValue) {
        operandValue.value = modelValue!.value;
    } else {
        operandValue.value = null;
    }

    if (operandType === OPERAND_TYPE_LITERAL && hasInitialValue) {
        initialAliasedNodeData.value = modelValue!.value as Record<
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
    (updatedOperandType, previousOperandType) => {
        if (previousOperandType === undefined) {
            return;
        }

        handleOperandTypeChange(updatedOperandType);
        emitUpdatedOperand();
    },
);

function hasInitialOperandValue(): boolean {
    if (modelValue === null || modelValue === undefined) {
        return false;
    }

    if (modelValue.value === undefined) {
        return false;
    }

    return true;
}

function handleOperandTypeChange(
    updatedOperandType: OperandPayloadTypeToken,
): void {
    const hasValueInModel = hasInitialOperandValue();

    if (updatedOperandType === OPERAND_TYPE_LITERAL) {
        operandValue.value = null;

        if (hasValueInModel) {
            initialAliasedNodeData.value = modelValue!.value as Record<
                string,
                unknown
            >;
        } else {
            initialAliasedNodeData.value = null;
        }

        return;
    }

    operandValue.value = [];
    initialAliasedNodeData.value = null;
}

function emitUpdatedOperand(): void {
    emit("update:modelValue", {
        type: operandType,
        value: operandValue.value,
    });
}

function handleGenericWidgetUpdate(
    updatedGenericWidgetValue: Record<string, unknown>,
): void {
    operandValue.value = updatedGenericWidgetValue;
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
