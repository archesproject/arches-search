<script setup lang="ts">
import { computed, inject, ref, watch, useId } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Button from "primevue/button";

import PathBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/PathBuilder.vue";
import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";
import TextSearchFilter from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/ClauseBuilder/components/TextSearchFilter.vue";
import { ClauseSubjectTypeToken } from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    GraphModel,
    AdvancedSearchFacet,
    LiteralClause,
    LiteralOperand,
    Node,
    PathSelection,
} from "@/arches_search/AdvancedSearch/types.ts";

type NodeWithCardinality = Node & {
    nodegroup_has_cardinality_n?: boolean;
};

const CLAUSE_QUANTIFIER_ANY = "ANY" as const;
const CLAUSE_QUANTIFIER_ALL = "ALL" as const;
const CLAUSE_QUANTIFIER_NONE = "NONE" as const;

const OPERAND_TYPE_LITERAL = "LITERAL" as const;

const { modelValue, anchorGraph } = defineProps<{
    modelValue: LiteralClause;
    anchorGraph: GraphModel;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", updatedClause: LiteralClause): void;
    (event: "request:remove"): void;
}>();

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeWithCardinality[]>>(
        "getNodesForGraphId",
    )!;

const { $gettext } = useGettext();

const subjectNode = ref<NodeWithCardinality | null>(null);
const subjectGraph = ref<GraphModel | null>(null);
const operandKeysByIndex = ref<string[]>([]);

const clauseQuantifierOptions = computed(() => [
    { label: $gettext("At least one"), value: CLAUSE_QUANTIFIER_ANY },
    { label: $gettext("Every"), value: CLAUSE_QUANTIFIER_ALL },
    { label: $gettext("No"), value: CLAUSE_QUANTIFIER_NONE },
]);

const subjectAnchorGraph = computed<GraphModel>(
    () =>
        graphs.value.find(
            (graph) => graph.slug === modelValue.subject.graph_slug,
        ) ?? anchorGraph,
);

const selectedSubjectNode = computed<PathSelection | null>(() => {
    if (
        modelValue.subject.type !== ClauseSubjectTypeToken.NODE ||
        !modelValue.subject.node_alias
    ) {
        return null;
    }
    return {
        graph_slug: modelValue.subject.graph_slug,
        node_alias: modelValue.subject.node_alias,
    };
});

const availableOperatorOptions = computed<AdvancedSearchFacet[]>(() => {
    if (modelValue.subject.type === ClauseSubjectTypeToken.SEARCH_MODELS) {
        return datatypesToAdvancedSearchFacets.value["string"] ?? [];
    }
    const datatype = subjectNode.value?.datatype;
    return datatype
        ? datatypesToAdvancedSearchFacets.value[datatype] ?? []
        : [];
});

const selectedAdvancedSearchFacet = computed<AdvancedSearchFacet | null>(() => {
    if (!modelValue.operator) return null;
    return (
        availableOperatorOptions.value.find(
            (facet) => facet.operator === modelValue.operator,
        ) ?? null
    );
});

watch(
    [
        () => modelValue.subject.type,
        () => modelValue.subject.graph_slug,
        () => modelValue.subject.node_alias,
    ],
    async ([subjectType, terminalGraphSlug, terminalNodeAlias]) => {
        subjectNode.value = null;
        subjectGraph.value = null;

        if (
            subjectType !== ClauseSubjectTypeToken.NODE ||
            !terminalGraphSlug ||
            !terminalNodeAlias
        ) {
            return;
        }

        const graphMatchingTerminalSlug = graphs.value.find(
            (graphModel) => graphModel.slug === terminalGraphSlug,
        );

        if (!graphMatchingTerminalSlug) {
            return;
        }

        subjectGraph.value = graphMatchingTerminalSlug;

        const allNodesForGraph = await getNodesForGraphId(
            graphMatchingTerminalSlug.graphid,
        );

        subjectNode.value =
            allNodesForGraph.find(
                (graphNode) => graphNode.alias === terminalNodeAlias,
            ) ?? null;
    },
    { immediate: true },
);

watch(
    () => subjectNode.value?.nodegroup_has_cardinality_n,
    (nodegroupHasCardinalityN) => {
        if (
            nodegroupHasCardinalityN === false &&
            modelValue.quantifier !== CLAUSE_QUANTIFIER_ANY
        ) {
            patchClause({ quantifier: CLAUSE_QUANTIFIER_ANY });
        }
    },
    { immediate: true },
);

function patchClause(partialClause: Partial<LiteralClause>): void {
    emit("update:modelValue", { ...modelValue, ...partialClause });
}

function ensureOperandKey(parameterIndex: number): string {
    if (!operandKeysByIndex.value[parameterIndex]) {
        operandKeysByIndex.value[parameterIndex] = useId();
    }
    return operandKeysByIndex.value[parameterIndex];
}

function handleSubjectUpdate(updatedSubject: PathSelection | null): void {
    patchClause({
        subject: {
            type: ClauseSubjectTypeToken.NODE,
            graph_slug:
                updatedSubject?.graph_slug ?? subjectAnchorGraph.value.slug,
            node_alias: updatedSubject?.node_alias ?? "",
            search_models: [],
        },
        operator: null,
        operands: [],
    });
}

function handleOperandUpdate(
    parameterIndex: number,
    updatedOperand: LiteralOperand | null,
): void {
    const updatedOperands = [...modelValue.operands];
    updatedOperands[parameterIndex] = updatedOperand ?? {
        type: OPERAND_TYPE_LITERAL,
        value: null,
    };
    patchClause({ operands: updatedOperands });
}

function handleOperatorChange(nextOperator: string | null): void {
    if (nextOperator === modelValue.operator) {
        return;
    }
    if (nextOperator === null) {
        patchClause({ operator: null, operands: [] });
        return;
    }
    const previousFacetArity = selectedAdvancedSearchFacet.value?.arity ?? 0;
    const nextFacetArity =
        availableOperatorOptions.value.find(
            (facet) => facet.operator === nextOperator,
        )?.arity ?? 0;
    if (previousFacetArity !== nextFacetArity) {
        patchClause({ operator: nextOperator, operands: [] });
        return;
    }
    patchClause({ operator: nextOperator });
}

function handleQuantifierChange(
    nextQuantifier: LiteralClause["quantifier"],
): void {
    if (modelValue.quantifier === nextQuantifier) {
        return;
    }
    patchClause({ quantifier: nextQuantifier });
}
</script>

<template>
    <div class="clause-builder">
        <div class="clause-main">
            <div class="clause-core-row">
                <PathBuilder
                    v-if="
                        modelValue.subject.type !==
                        ClauseSubjectTypeToken.SEARCH_MODELS
                    "
                    class="clause-subject-path"
                    :selected-node="selectedSubjectNode"
                    :graph-slugs="[subjectAnchorGraph.slug]"
                    @update:selected-node="handleSubjectUpdate"
                />
                <TextSearchFilter
                    v-if="
                        modelValue.subject.type ===
                        ClauseSubjectTypeToken.SEARCH_MODELS
                    "
                    :model-value="modelValue"
                    :available-operator-options="availableOperatorOptions"
                    @update:model-value="
                        emit('update:modelValue', $event as LiteralClause)
                    "
                />

                <Select
                    v-else-if="subjectNode?.nodegroup_has_cardinality_n"
                    :model-value="modelValue.quantifier"
                    class="clause-quantifier-select"
                    :options="clauseQuantifierOptions"
                    option-label="label"
                    option-value="value"
                    @update:model-value="handleQuantifierChange"
                />

                <Select
                    v-if="
                        modelValue.subject.type !==
                        ClauseSubjectTypeToken.SEARCH_MODELS
                    "
                    :model-value="modelValue.operator"
                    class="clause-operator-select"
                    :options="availableOperatorOptions"
                    option-label="label"
                    option-value="operator"
                    :disabled="availableOperatorOptions.length === 0"
                    :placeholder="$gettext('Select an operator...')"
                    @update:model-value="handleOperatorChange"
                />

                <div
                    v-if="
                        modelValue.subject.type !==
                            ClauseSubjectTypeToken.SEARCH_MODELS &&
                        selectedAdvancedSearchFacet?.arity &&
                        subjectNode &&
                        subjectGraph
                    "
                    class="clause-operands-row"
                >
                    <ClauseOperandBuilder
                        v-for="parameterIndex in selectedAdvancedSearchFacet.arity"
                        :key="ensureOperandKey(parameterIndex - 1)"
                        :model-value="
                            modelValue.operands[parameterIndex - 1] ?? null
                        "
                        :subject-terminal-node="subjectNode"
                        :subject-terminal-graph="subjectGraph"
                        :operand-type="OPERAND_TYPE_LITERAL"
                        @update:model-value="
                            handleOperandUpdate(
                                parameterIndex - 1,
                                $event as LiteralOperand,
                            )
                        "
                    />
                </div>
            </div>

            <div
                v-if="subjectNode?.nodegroup_has_cardinality_n"
                class="clause-cardinality-subtext"
            >
                {{
                    $gettext(
                        "This attribute can have multiple values. Please select how you want to filter values.",
                    )
                }}
            </div>
        </div>

        <Button
            class="clause-remove-button"
            icon="pi pi-times"
            severity="danger"
            variant="text"
            type="button"
            :aria-label="$gettext('Remove filter')"
            @click="emit('request:remove')"
        />
    </div>
</template>

<style scoped>
.clause-builder {
    font-size: 1rem;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: flex-start;
}

.clause-main {
    grid-column: 1 / 3;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.clause-core-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.clause-operands-row {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.clause-cardinality-subtext {
    margin-inline-start: 0.5rem;
    margin-block-start: 1rem;
    font-size: 1rem;
    line-height: 1.25;
    opacity: 0.75;
}

.clause-remove-button {
    grid-column: 3;
    justify-self: flex-end;
}
</style>
