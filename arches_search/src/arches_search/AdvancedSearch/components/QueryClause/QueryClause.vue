<script setup lang="ts">
import {
    computed,
    defineEmits,
    defineProps,
    inject,
    ref,
    useId,
    watch,
} from "vue";

import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Button from "primevue/button";

import PathBuilder from "@/arches_search/AdvancedSearch/components/QueryClause/components/PathBuilder.vue";
import OperandBuilder from "@/arches_search/AdvancedSearch/components/QueryClause/components/OperandBuilder.vue";

import { updateClause } from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

import type { Ref } from "vue";
import type {
    AdvancedSearchFacet,
    Node,
} from "@/arches_search/AdvancedSearch/types.ts";
import type { Clause } from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

const { $gettext } = useGettext();

const props = defineProps<{
    clause: Clause;
    groupSelectedGraph: { [key: string]: unknown };
    parentGroupSelectedGraph?: { [key: string]: unknown } | undefined;
}>();

const emit = defineEmits<{
    (e: "request:removeClause", targetClause: Clause): void;
}>();

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;
const graphs = inject<Ref<Record<string, unknown>[]>>("graphs")!;
const getNodesForGraphId =
    inject<(graphId: string) => Promise<Node[]>>("getNodesForGraphId")!;

const operator = ref<string | null>(null);
const subjectTerminalNode = ref<Node | null>(null);
const subjectTerminalGraph = ref<Record<string, unknown> | null>(null);

const subjectPathSequence = computed<Array<[string, string]>>(() => {
    return props.clause.subject ?? [];
});

const subjectPathTerminalGraphSlugNodeAlias = computed<[string, string] | null>(
    () => {
        if (subjectPathSequence.value.length === 0) {
            return null;
        }
        return subjectPathSequence.value[subjectPathSequence.value.length - 1];
    },
);

const operatorOptions = computed(() => {
    if (!subjectTerminalNode.value?.datatype) {
        return [];
    }
    return (
        datatypesToAdvancedSearchFacets.value[
            subjectTerminalNode.value.datatype
        ] ?? []
    );
});

const selectedAdvancedSearchFacet = computed(() => {
    if (!operator.value) {
        return null;
    }
    return (
        operatorOptions.value.find((advancedSearchFacet) => {
            return advancedSearchFacet.operator === operator.value;
        }) ?? null
    );
});

watch(
    () => props.clause.operator,
    (nextOperator) => {
        operator.value = nextOperator ?? null;
    },
    { immediate: true },
);

watch(
    subjectPathTerminalGraphSlugNodeAlias,
    async (updatedSubjectTerminalGraphSlugNodeAlias) => {
        subjectTerminalNode.value = null;
        subjectTerminalGraph.value = null;

        if (!updatedSubjectTerminalGraphSlugNodeAlias) {
            return;
        }

        const [terminalGraphSlug, terminalNodeAlias] =
            updatedSubjectTerminalGraphSlugNodeAlias;

        if (!terminalGraphSlug || !terminalNodeAlias) {
            return;
        }

        const terminalGraph = graphs.value.find(
            (graph) => graph.slug === terminalGraphSlug,
        );
        const nodes = await getNodesForGraphId(
            terminalGraph!.graphid as string,
        );

        subjectTerminalGraph.value = terminalGraph ?? null;
        subjectTerminalNode.value =
            nodes.find((node) => node.alias === terminalNodeAlias) ?? null;
    },
    { immediate: true },
);

watch(operator, (nextOperator, previousOperator) => {
    if (nextOperator === previousOperator) {
        return;
    }

    updateClause(props.clause, { operator: nextOperator });
});

function onSubjectUpdate(updatedSubjectPathSequence: Array<[string, string]>) {
    if (props.clause.subject === updatedSubjectPathSequence) {
        return;
    }

    updateClause(props.clause, {
        subject: updatedSubjectPathSequence,
        operator: null,
        operands: [],
    });
}

function onOperandUpdate(parameterIndex: number, updatedOperand: unknown) {
    const currentOperands = props.clause.operands ?? [];
    const updatedOperands = [...currentOperands];

    updatedOperands[parameterIndex] = updatedOperand as {
        [key: string]: unknown;
    };

    updateClause(props.clause, { operands: updatedOperands });
}

function onRemoveSelf() {
    emit("request:removeClause", props.clause);
}
</script>

<template>
    <div class="query-clause">
        <Button
            style="align-self: flex-end"
            icon="pi pi-times"
            severity="danger"
            @click="onRemoveSelf"
        />

        <div>
            <!-- :key is here to force PathBuilder to remount on subjectPathSequence change, to prevent an infinite recursion loop -->
            <PathBuilder
                :key="
                    subjectPathSequence
                        .map(
                            ([graphSlug, nodeAlias]) =>
                                `${graphSlug}:${nodeAlias}`,
                        )
                        .join(':')
                "
                :path-sequence="subjectPathSequence"
                :anchor-graph="groupSelectedGraph"
                @update:path-sequence="onSubjectUpdate"
            />

            <Select
                v-model="operator"
                :options="operatorOptions"
                option-label="label"
                option-value="operator"
                :disabled="operatorOptions.length === 0"
                :placeholder="$gettext('Select an operator...')"
            />

            <div
                v-if="
                    selectedAdvancedSearchFacet &&
                    selectedAdvancedSearchFacet.arity > 0
                "
            >
                <!-- prettier-ignore -->
                <OperandBuilder
                    v-for="parameterIndex in selectedAdvancedSearchFacet.arity"
                    :key="useId() + parameterIndex"
                    :model-value="props.clause.operands?.[parameterIndex - 1]"
                    :group-selected-graph="groupSelectedGraph"
                    :parent-group-selected-graph="
                        props.parentGroupSelectedGraph
                    "
                    :subject-terminal-node="subjectTerminalNode!"
                    :subject-terminal-graph="subjectTerminalGraph!"
                    @update:model-value="
                        onOperandUpdate(parameterIndex - 1, $event)
                    "
                />
            </div>
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
    display: flex;
    flex-direction: column;
}
</style>
