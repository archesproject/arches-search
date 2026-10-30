<script setup lang="ts">
import { computed, useTemplateRef } from "vue";

import MapComponent from "@/arches_vue_components/components/MapComponent/MapComponent.vue";
import MapToolsPanel from "@/arches_vue_components/components/MapComponent/components/MapToolsPanel/MapToolsPanel.vue";

import { useDefaultMapInteractionTools } from "@/arches_vue_components/components/MapComponent/composables/useDefaultMapInteractionTools.ts";
import { isFeatureCollection } from "@/arches_search/AdvancedSearch/utils/query-builder.ts";

import type { FeatureCollection } from "geojson";
import type { LiteralClause } from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_CLAUSE_EVENT = "update:clause" as const;
const OPERAND_TYPE_LITERAL = "LITERAL" as const;

const { clause } = defineProps<{
    clause: LiteralClause;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_CLAUSE_EVENT, updatedClause: LiteralClause): void;
}>();

const mapComponentRef =
    useTemplateRef<InstanceType<typeof MapComponent>>("mapComponent");
const mapToolsTool = useDefaultMapInteractionTools().find(
    (tool) => tool.component === MapToolsPanel,
);

const drawnArea = computed<FeatureCollection | null>(() => {
    const operandValue = clause.operands[0]?.value;
    if (isFeatureCollection(operandValue)) {
        return operandValue;
    }
    return null;
});

function onMapReady(): void {
    if (mapToolsTool) {
        mapComponentRef.value?.openPanel(mapToolsTool.name);
    }
    if (drawnArea.value && drawnArea.value.features.length > 0) {
        mapComponentRef.value?.context?.addFeatures(drawnArea.value.features);
    }
}

function onMapUpdate(updatedValue: FeatureCollection): void {
    if (updatedValue.features.length === 0) {
        emit(UPDATE_CLAUSE_EVENT, { ...clause, operands: [] });
        return;
    }
    emit(UPDATE_CLAUSE_EVENT, {
        ...clause,
        operands: [{ type: OPERAND_TYPE_LITERAL, value: updatedValue }],
    });
}
</script>

<template>
    <div class="map-operand-editor">
        <MapComponent
            ref="mapComponent"
            :value="drawnArea"
            @update:value="onMapUpdate"
            @ready="onMapReady"
        />
    </div>
</template>

<style scoped>
.map-operand-editor {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
}
</style>
