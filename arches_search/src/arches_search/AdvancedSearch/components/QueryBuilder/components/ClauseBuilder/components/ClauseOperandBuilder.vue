<script setup lang="ts">
import { ref, watchEffect } from "vue";

import GenericWidget from "@/arches_vue_components/generics/GenericWidget/GenericWidget.vue";

import {
    isLabelList,
    referenceValuesForLabels,
} from "@/arches_search/AdvancedSearch/utils/reference-labels.ts";

import { OPERAND_TYPE_LITERAL } from "@/arches_search/AdvancedSearch/types.ts";

import type { AliasedNodeData } from "@/arches_vue_components/types.ts";
import type {
    GraphModel,
    LiteralOperand,
    Node,
} from "@/arches_search/AdvancedSearch/types.ts";

const DATATYPE_REFERENCE = "reference";
const UPDATE_MODEL_VALUE = "update:modelValue" as const;

const { modelValue, subjectTerminalNode, subjectTerminalGraph } = defineProps<{
    modelValue: LiteralOperand | null;
    subjectTerminalNode: Node;
    subjectTerminalGraph: GraphModel;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_MODEL_VALUE, updatedOperand: LiteralOperand): void;
}>();

const initialValue = modelValue?.value ?? null;
const initialAliasedNodeData = ref<AliasedNodeData | undefined>(
    buildInitialAliasedNodeData(),
);
const referenceLabelLookup = labelsToLookUp();
const isLookingUpLabels = ref(referenceLabelLookup !== null);

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
    if (modelValue?.value == null) {
        return undefined;
    }
    return {
        node_value: modelValue.value,
        display_value: modelValue.display_value ?? "",
        details: [],
    };
}

function handleGenericWidgetUpdate(
    updatedAliasedNodeData: AliasedNodeData,
): void {
    emit(UPDATE_MODEL_VALUE, {
        type: OPERAND_TYPE_LITERAL,
        value: updatedAliasedNodeData.node_value,
        display_value: updatedAliasedNodeData.display_value || undefined,
    });
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
