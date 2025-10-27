<script setup lang="ts">
import {
    computed,
    defineEmits,
    defineProps,
    ref,
    watch,
    watchEffect,
    nextTick,
} from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import GenericWidget from "@/arches_component_lab/generics/GenericWidget/GenericWidget.vue";
import PathBuilder from "@/arches_search/AdvancedSearch/components/QueryClause/components/PathBuilder.vue";

import type { Node } from "@/arches_search/AdvancedSearch/types.ts";

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

const isSyncingFromProps = ref(false);
const operandType = ref<OperandType>();
const operandValue = ref<unknown>();

const pathSequenceSeedGraph = computed<Record<string, unknown>>(() => {
    if (operandType.value === PARENT) {
        return parentGroupSelectedGraph!;
    } else {
        return groupSelectedGraph;
    }
});

watchEffect(() => {
    if (!modelValue) {
        operandType.value = LITERAL;
        operandValue.value = null;

        return;
    }

    isSyncingFromProps.value = true;
    operandType.value = modelValue.type as OperandType;
    operandValue.value = modelValue.value;

    nextTick(() => {
        isSyncingFromProps.value = false;
    });
});

watch([operandType, operandValue], ([updatedOperandType, nextValue]) => {
    if (isSyncingFromProps.value) {
        return;
    }

    emit("update:modelValue", {
        type: updatedOperandType,
        value: nextValue,
    } as Operand);
});

function coerceGenericWidgetValue(
    genericWidgetValue: Record<string, unknown>,
    datatype: string,
): unknown {
    if (datatype === "string") {
        return genericWidgetValue.display_value;
    } else {
        return genericWidgetValue.node_value;
    }
}

function onOperandTypeUpdate(updatedOperandType: OperandType) {
    if (operandType.value === updatedOperandType) {
        return;
    }

    operandType.value = updatedOperandType;
    operandValue.value = updatedOperandType === LITERAL ? null : [];
}

function onGenericWidgetUpdate(
    updatedGenericWidgetValue: Record<string, unknown>,
) {
    operandValue.value = coerceGenericWidgetValue(
        updatedGenericWidgetValue,
        subjectTerminalNode.datatype,
    );
}

function onPathSequenceUpdate(updatedPathSequence: Array<[string, string]>) {
    if (isSyncingFromProps.value) {
        return;
    }

    operandValue.value = updatedPathSequence;
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
            :aliased-node-data="{ node_value: operandValue }"
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
