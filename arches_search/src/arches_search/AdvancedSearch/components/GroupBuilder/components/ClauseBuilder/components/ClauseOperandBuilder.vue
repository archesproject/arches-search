<script setup lang="ts">
import { computed, ref, watch, watchEffect } from "vue";

import GenericWidget from "@/arches_component_lab/generics/GenericWidget/GenericWidget.vue";
import PathBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/PathBuilder.vue";

import type { Node } from "@/arches_search/AdvancedSearch/types.ts";

const OPERAND_TYPE_LITERAL = "LITERAL";
const OPERAND_TYPE_PATH = "PATH";

type OperandPayloadTypeToken =
    | typeof OPERAND_TYPE_LITERAL
    | typeof OPERAND_TYPE_PATH;

type OperandPayload = {
    type: OperandPayloadTypeToken;
    value: unknown;
} | null;

type GraphSummary = {
    graphid: string;
    slug: string;
    name: string;
    [key: string]: unknown;
};

const emit = defineEmits<{
    (event: "update:modelValue", updatedOperand: OperandPayload): void;
}>();

const {
    modelValue,
    anchorGraph,
    subjectTerminalNode,
    subjectTerminalGraph,
    operandType,
} = defineProps<{
    modelValue: OperandPayload;
    anchorGraph: GraphSummary;
    subjectTerminalNode: Node;
    subjectTerminalGraph: GraphSummary;
    operandType: OperandPayloadTypeToken;
}>();

const operandValue = ref<unknown>(null);
const initialAliasedNodeData = ref<Record<string, unknown> | null>(null);
const hasInitializedFromModel = ref(false);

const coercedPathSequence = computed<[string, string][]>(() => {
    if (Array.isArray(operandValue.value)) {
        return operandValue.value as [string, string][];
    }

    return [];
});

watchEffect(() => {
    if (hasInitializedFromModel.value) {
        return;
    }

    const hasInitialValue = hasInitialOperandValue();

    if (hasInitialValue) {
        operandValue.value = modelValue!.value;
    } else {
        if (operandType === OPERAND_TYPE_PATH) {
            operandValue.value = [];
        } else {
            operandValue.value = null;
        }
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

function handlePathSequenceUpdate(
    updatedPathSequence: [string, string][],
): void {
    operandValue.value = updatedPathSequence;
    emitUpdatedOperand();
}
</script>

<template>
    <div class="clause-operand-builder">
        <GenericWidget
            v-if="operandType === OPERAND_TYPE_LITERAL"
            class="clause-operand-editor"
            mode="edit"
            :graph-slug="subjectTerminalGraph.slug"
            :node-alias="subjectTerminalNode.alias"
            :should-show-label="false"
            :aliased-node-data="initialAliasedNodeData || undefined"
            :compact="true"
            @update:value="handleGenericWidgetUpdate"
        />

        <PathBuilder
            v-else-if="operandType === OPERAND_TYPE_PATH"
            class="clause-operand-editor"
            :anchor-graph="anchorGraph"
            :path-sequence="coercedPathSequence"
            :show-anchor-graph-dropdown="true"
            @update:path-sequence="handlePathSequenceUpdate"
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
