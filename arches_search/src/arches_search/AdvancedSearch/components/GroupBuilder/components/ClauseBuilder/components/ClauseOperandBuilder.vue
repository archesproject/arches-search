<script setup lang="ts">
import { computed, defineEmits, defineProps, ref, watch } from "vue";

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
    slug?: string;
    [key: string]: unknown;
};

const props = defineProps<{
    modelValue: OperandPayload;
    anchorGraph: GraphSummary;
    parentGroupAnchorGraph?: GraphSummary;
    subjectTerminalNode: Node;
    subjectTerminalGraph: GraphSummary;
    operandType: OperandPayloadTypeToken;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", updatedOperand: OperandPayload): void;
}>();

const operandValue = ref<unknown>(null);
const literalAliasedNodeData = ref<Record<string, unknown> | null>(null);

const pathSequenceSeedGraph = computed<GraphSummary>(() => {
    return props.anchorGraph;
});

const isLiteralOperandActive = computed<boolean>(() => {
    return props.operandType === OPERAND_TYPE_LITERAL;
});

const isPathOperandActive = computed<boolean>(() => {
    return props.operandType === OPERAND_TYPE_PATH;
});

const coercedPathSequence = computed<[string, string][]>(() => {
    if (Array.isArray(operandValue.value)) {
        return operandValue.value as [string, string][];
    }
    return [];
});

watch(
    () => props.modelValue,
    (updatedOperand) => {
        if (!updatedOperand) {
            if (props.operandType === OPERAND_TYPE_PATH) {
                operandValue.value = [];
                literalAliasedNodeData.value = null;
                emitUpdatedOperand();
            } else {
                operandValue.value = null;
                literalAliasedNodeData.value = null;
                emitUpdatedOperand();
            }
            return;
        }

        operandValue.value = updatedOperand.value;

        if (props.operandType === OPERAND_TYPE_LITERAL) {
            literalAliasedNodeData.value = buildAliasedNodeDataFromRawValue(
                operandValue.value,
                props.subjectTerminalNode.datatype,
            );
        } else {
            literalAliasedNodeData.value = null;
        }
    },
    { immediate: true },
);

watch(
    () => props.operandType,
    (updatedOperandType, previousOperandType) => {
        if (updatedOperandType === previousOperandType) {
            return;
        }

        if (updatedOperandType === OPERAND_TYPE_LITERAL) {
            operandValue.value = null;
            literalAliasedNodeData.value = null;
        } else {
            operandValue.value = [];
            literalAliasedNodeData.value = null;
        }

        emitUpdatedOperand();
    },
);

function buildAliasedNodeDataFromRawValue(
    rawValue: unknown,
    datatype: string,
): Record<string, unknown> | null {
    if (rawValue === null || rawValue === undefined) {
        return null;
    }

    if (datatype === "resource-instance") {
        return {
            node_value: {
                resourceId: rawValue,
            },
        };
    }

    if (datatype === "resource-instance-list") {
        const resourceIds = Array.isArray(rawValue) ? rawValue : [rawValue];
        return {
            node_value: resourceIds.map((resourceId) => {
                return { resourceId };
            }),
        };
    }

    if (datatype === "string") {
        const coercedString = String(rawValue);
        return {
            node_value: coercedString,
            display_value: coercedString,
        };
    }

    return {
        node_value: rawValue,
    };
}

function coerceGenericWidgetValueToOperandValue(
    genericWidgetValue: Record<string, unknown>,
    datatype: string,
): unknown {
    if (datatype === "resource-instance") {
        const widgetNodeValue = genericWidgetValue.node_value as Record<
            string,
            unknown
        >;
        return widgetNodeValue.resourceId;
    }

    if (datatype === "resource-instance-list") {
        const widgetNodeValue = genericWidgetValue.node_value as unknown[];
        return widgetNodeValue.map((item) => {
            const listItem = item as Record<string, unknown>;
            return listItem.resourceId;
        });
    }

    if (datatype === "string") {
        return (genericWidgetValue as { display_value: unknown }).display_value;
    }

    return (genericWidgetValue as { node_value: unknown }).node_value;
}

function emitUpdatedOperand(): void {
    emit("update:modelValue", {
        type: props.operandType,
        value: operandValue.value,
    });
}

function handleGenericWidgetUpdate(
    updatedGenericWidgetValue: Record<string, unknown>,
): void {
    literalAliasedNodeData.value = updatedGenericWidgetValue;
    operandValue.value = coerceGenericWidgetValueToOperandValue(
        updatedGenericWidgetValue,
        props.subjectTerminalNode.datatype,
    );
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
            v-if="isLiteralOperandActive"
            class="clause-operand-editor"
            mode="edit"
            :graph-slug="subjectTerminalGraph.slug as string"
            :node-alias="subjectTerminalNode.alias"
            :should-show-label="false"
            :aliased-node-data="literalAliasedNodeData || undefined"
            @update:value="handleGenericWidgetUpdate"
        />

        <PathBuilder
            v-else-if="isPathOperandActive"
            class="clause-operand-editor"
            :anchor-graph="pathSequenceSeedGraph"
            :path-sequence="coercedPathSequence"
            @update:path-sequence="handlePathSequenceUpdate"
        />
    </div>
</template>

<style scoped>
.clause-operand-builder {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1rem;
}

.clause-operand-editor {
    flex: 1 1 auto;
    min-width: 8rem;
}
</style>
