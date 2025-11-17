<script setup lang="ts">
import { computed, defineEmits, defineProps, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import GenericWidget from "@/arches_component_lab/generics/GenericWidget/GenericWidget.vue";
import PathBuilder from "@/arches_search/AdvancedSearch/components/QueryClause/components/PathBuilder.vue";

import type { Node } from "@/arches_search/AdvancedSearch/types";

const LITERAL = "LITERAL";
const SELF = "SELF";
const PARENT = "PARENT";
const RESULTSET = "RESULTSET";

type LiteralOperand = { type: typeof LITERAL; value: unknown };
type SelfOperand = { type: typeof SELF; value: [string, string][] };
type ParentOperand = { type: typeof PARENT; value: [string, string][] };
type ResultsetOperand = { type: typeof RESULTSET; value: null };

type OperandType =
    | typeof SELF
    | typeof LITERAL
    | typeof PARENT
    | typeof RESULTSET;

type Operand =
    | LiteralOperand
    | SelfOperand
    | ParentOperand
    | ResultsetOperand
    | null;

const { $gettext } = useGettext();

const {
    modelValue,
    groupSelectedGraph,
    parentGroupSelectedGraph,
    subjectTerminalNode,
    subjectTerminalGraph,
} = defineProps<{
    modelValue: Record<string, unknown> | null | undefined;
    groupSelectedGraph: Record<string, unknown>;
    parentGroupSelectedGraph?: Record<string, unknown>;
    subjectTerminalNode: Node;
    subjectTerminalGraph: Record<string, unknown>;
}>();

const emit = defineEmits<{ (e: "update:modelValue", value: Operand): void }>();

const operandOriginOptions = [
    { label: $gettext("LITERAL"), value: LITERAL },
    { label: $gettext("SELF"), value: SELF },
    {
        label: $gettext("PARENT"),
        value: PARENT,
        disabled: !parentGroupSelectedGraph,
    },
    { label: $gettext("RESULTSET"), value: RESULTSET },
];

const operandType = ref<OperandType>(LITERAL);
const operandValue = ref<unknown>(null);
const literalAliasedNodeData = ref<Record<string, unknown> | undefined>();

const pathSequenceSeedGraph = computed<Record<string, unknown>>(() => {
    if (operandType.value === PARENT) {
        return parentGroupSelectedGraph!;
    } else {
        return groupSelectedGraph;
    }
});

function buildAliasedNodeDataFromOperandValue(
    rawValue: unknown,
    datatype: string,
): Record<string, unknown> | undefined {
    if (rawValue === null || rawValue === undefined) {
        return undefined;
    }

    if (datatype === "resource-instance") {
        return { node_value: { resourceId: rawValue } };
    }

    if (datatype === "resource-instance-list") {
        const resourceIds = Array.isArray(rawValue) ? rawValue : [rawValue];
        return {
            node_value: resourceIds.map((resourceId) => ({ resourceId })),
        };
    }

    if (datatype === "string") {
        const stringValue = String(rawValue);
        return { node_value: stringValue, display_value: stringValue };
    }

    return { node_value: rawValue };
}

watch(
    () => modelValue,
    (nextModel) => {
        if (!nextModel) {
            operandType.value = LITERAL;
            operandValue.value = null;
            literalAliasedNodeData.value = undefined;
            return;
        }

        operandType.value = nextModel.type as OperandType;
        operandValue.value = nextModel.value;

        if (operandType.value === LITERAL) {
            literalAliasedNodeData.value = buildAliasedNodeDataFromOperandValue(
                operandValue.value,
                subjectTerminalNode.datatype,
            );
        } else {
            literalAliasedNodeData.value = undefined;
        }
    },
    { immediate: true },
);

function coerceGenericWidgetValue(
    genericWidgetValue: Record<string, unknown>,
    datatype: string,
): unknown {
    if (datatype === "resource-instance") {
        const genericWidgetNodeValue = genericWidgetValue.node_value as {
            [key: string]: unknown;
        };
        return genericWidgetNodeValue.resourceId;
    } else if (datatype === "resource-instance-list") {
        const nodeValue = genericWidgetValue.node_value as unknown[];
        return [
            ...nodeValue.map((listItem) => {
                return (listItem as { [key: string]: unknown }).resourceId;
            }),
        ];
    } else if (datatype === "string") {
        return (genericWidgetValue as { display_value: unknown }).display_value;
    } else {
        return (genericWidgetValue as { node_value: unknown }).node_value;
    }
}

function onOperandTypeUpdate(updatedOperandType: OperandType) {
    if (operandType.value === updatedOperandType) {
        return;
    }

    operandType.value = updatedOperandType;

    if (updatedOperandType === LITERAL) {
        literalAliasedNodeData.value =
            literalAliasedNodeData.value ??
            buildAliasedNodeDataFromOperandValue(
                operandValue.value,
                subjectTerminalNode.datatype,
            );
        operandValue.value = operandValue.value ?? null;
    } else {
        literalAliasedNodeData.value = undefined;
        operandValue.value = updatedOperandType === RESULTSET ? null : [];
    }

    emit("update:modelValue", {
        type: operandType.value,
        value: operandValue.value,
    } as Operand);
}

function onGenericWidgetUpdate(
    updatedGenericWidgetValue: Record<string, unknown>,
) {
    literalAliasedNodeData.value = updatedGenericWidgetValue;
    operandValue.value = coerceGenericWidgetValue(
        updatedGenericWidgetValue,
        subjectTerminalNode.datatype,
    );

    emit("update:modelValue", {
        type: operandType.value,
        value: operandValue.value,
    } as Operand);
}

function onPathSequenceUpdate(updatedPathSequence: Array<[string, string]>) {
    operandValue.value = updatedPathSequence;

    emit("update:modelValue", {
        type: operandType.value,
        value: operandValue.value,
    } as Operand);
}
</script>

<template>
    <div class="operand-builder">
        <Select
            option-disabled="disabled"
            option-label="label"
            option-value="value"
            :model-value="operandType"
            :options="operandOriginOptions"
            @update:model-value="onOperandTypeUpdate"
        />

        <!-- prettier-ignore -->
        <GenericWidget
            v-if="operandType === LITERAL"
            mode="edit"
            :graph-slug="(subjectTerminalGraph.slug as string)"
            :node-alias="subjectTerminalNode.alias"
            :should-show-label="false"
            :aliased-node-data="literalAliasedNodeData"
            @update:value="onGenericWidgetUpdate"
        />

        <!-- prettier-ignore -->
        <PathBuilder
            v-else-if="operandType !== RESULTSET"
            :anchor-graph="pathSequenceSeedGraph"
            :path-sequence="(operandValue as [string, string][])"
            @update:path-sequence="onPathSequenceUpdate"
        />
    </div>
</template>

<style scoped>
.operand-builder {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}
</style>
