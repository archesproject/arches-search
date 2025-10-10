<script setup lang="ts">
import { computed, defineEmits, defineProps, inject, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Button from "primevue/button";
import GenericWidget from "@/arches_component_lab/generics/GenericWidget/GenericWidget.vue";

import type { Ref } from "vue";
import {
    updateClause,
    type Clause,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";
import type {
    AdvancedSearchFacet,
    GraphModel,
    Node,
} from "@/arches_search/AdvancedSearch/types.ts";

const DATATYPE_TO_SEARCH_TABLE: { [key: string]: string } = {
    string: "term",
    number: "numeric",
};

const { $gettext } = useGettext();

const { clause } = defineProps<{ clause: Clause }>();

const emit = defineEmits<{
    (e: "request:removeClause", targetClause: Clause): void;
}>();

const facetsByDatatype = inject<Ref<{ [key: string]: AdvancedSearchFacet[] }>>(
    "advancedSearchFacets",
)!;
const selectedGraph = inject<Ref<GraphModel | null>>("selectedGraph")!;
const selectedGraphNodes = inject<Ref<Node[]>>("selectedGraphNodes")!;

const selectedNode = computed(() => {
    return (
        selectedGraphNodes.value.find((candidateNode) => {
            return candidateNode["alias"] === clause.node_alias;
        }) ?? null
    );
});

const selectedOperatorOptions = computed(() => {
    const datatype = selectedNode.value?.datatype ?? null;

    if (!datatype) {
        return [];
    }

    const facets = facetsByDatatype.value?.[datatype] ?? [];
    return facets.map((facetItem) => {
        return {
            label: facetItem.label,
            value: facetItem.operator,
        };
    });
});

const selectedAdvancedSearchFacet = computed<AdvancedSearchFacet | null>(() => {
    const datatype = selectedNode.value?.datatype ?? null;

    if (!datatype) {
        return null;
    }

    const facetList = facetsByDatatype.value?.[datatype] ?? [];
    return (
        facetList.find((facetItem) => {
            return facetItem.operator === clause.operator;
        }) ?? null
    );
});

watch(
    selectedNode,
    (newSelectedNode) => {
        if (!newSelectedNode) {
            updateClause(clause, {
                datatype: null,
                search_table: null,
            });
            return;
        }

        updateClause(clause, {
            datatype: newSelectedNode.datatype,
            search_table:
                DATATYPE_TO_SEARCH_TABLE[newSelectedNode.datatype] ?? null,
        });
    },
    { immediate: true },
);

watch(
    () => clause.node_alias,
    (newNodeAlias, previousNodeAlias) => {
        if (
            previousNodeAlias === undefined ||
            newNodeAlias === previousNodeAlias
        ) {
            return;
        }

        updateClause(clause, {
            operator: null,
            params: [],
        });
    },
);

watch(
    selectedAdvancedSearchFacet,
    (facet) => {
        if (!facet) {
            return;
        }

        const currentParams = Array.isArray(clause.params) ? clause.params : [];

        updateClause(clause, {
            params: Array.from({ length: facet.arity }, (_, parameterIndex) => {
                return currentParams[parameterIndex];
            }),
        });
    },
    { immediate: true },
);

function updateParameterAtIndex(parameterIndex: number, newValue: unknown) {
    const workingParams = [...clause.params];
    workingParams[parameterIndex] = foo(newValue as Record<string, unknown>);

    updateClause(clause, {
        params: workingParams,
    });
}

// TODO: Move to own util
function foo(valueFromGenericWidget: Record<string, unknown>) {
    const datatype = selectedNode.value?.datatype ?? null;

    if (datatype === "string") {
        return valueFromGenericWidget?.["display_value"];
    } else {
        return valueFromGenericWidget?.["node_value"];
    }
}

function onRemoveSelf() {
    emit("request:removeClause", clause);
}
</script>

<template>
    <div class="query-clause">
        <div style="display: flex; justify-content: flex-end">
            <Button
                icon="pi pi-times"
                severity="danger"
                @click="onRemoveSelf"
            />
        </div>

        <div>
            <Select
                option-label="name"
                option-value="alias"
                :model-value="clause.node_alias"
                :options="selectedGraphNodes"
                :placeholder="$gettext('Select a node...')"
                @update:model-value="
                    (value) => updateClause(clause, { node_alias: value })
                "
            />

            <Select
                option-label="label"
                option-value="value"
                :model-value="clause.operator"
                :disabled="selectedOperatorOptions.length === 0"
                :options="selectedOperatorOptions"
                :placeholder="$gettext('Select an operator...')"
                @update:model-value="
                    (value) => updateClause(clause, { operator: value })
                "
            />
        </div>

        <div
            v-if="
                selectedAdvancedSearchFacet &&
                selectedAdvancedSearchFacet.arity > 0
            "
        >
            <GenericWidget
                v-for="parameterIndex in selectedAdvancedSearchFacet.arity"
                :key="`facet-param-${parameterIndex - 1}`"
                mode="edit"
                :graph-slug="selectedGraph!.slug"
                :node-alias="clause.node_alias!"
                :should-show-label="false"
                :aliased-node-data="{
                    node_value: clause.params?.[parameterIndex - 1] ?? null,
                }"
                @update:value="
                    updateParameterAtIndex(parameterIndex - 1, $event)
                "
            />
        </div>
    </div>
</template>

<style scoped>
.query-clause {
    border: 0.125rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
    color: var(--p-text-color);
    padding: 1rem;
}
</style>
