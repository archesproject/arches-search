<script setup lang="ts">
import { computed, inject, ref, watch, useId } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Button from "primevue/button";
import InputText from "primevue/inputtext";

import PathBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/PathBuilder.vue";
import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";
import { ClauseSubjectTypeToken } from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    GraphModel,
    AdvancedSearchFacet,
    ClauseSubject,
    Node,
    PathSelection,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type NodeWithCardinality = Node & {
    nodegroup_has_cardinality_n?: boolean;
};

type OperandPayload = {
    type: "LITERAL" | "PATH";
    value: unknown;
    display_value?: string;
};

type ClausePayload = {
    type: "LITERAL";
    quantifier: "ANY" | "ALL" | "NONE";
    subject: ClauseSubject;
    operator: string | null;
    operands: OperandPayload[];
};

const CLAUSE_QUANTIFIER_ANY = "ANY" as const;
const CLAUSE_QUANTIFIER_ALL = "ALL" as const;
const CLAUSE_QUANTIFIER_NONE = "NONE" as const;

const OPERAND_TYPE_LITERAL = "LITERAL" as const;

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeWithCardinality[]>>(
        "getNodesForGraphId",
    )!;

const { modelValue, anchorGraph } = defineProps<{
    modelValue: ClausePayload;
    anchorGraph: GraphModel;
}>();

const emit = defineEmits<{
    "update:modelValue": [updatedClause: ClausePayload];
    "request:remove": [];
}>();

const clauseQuantifierOptions = computed(() => {
    return [
        { label: $gettext("At least one"), value: CLAUSE_QUANTIFIER_ANY },
        { label: $gettext("Every"), value: CLAUSE_QUANTIFIER_ALL },
        { label: $gettext("No"), value: CLAUSE_QUANTIFIER_NONE },
    ];
});

const subjectNode = ref<NodeWithCardinality | null>(null);
const subjectGraph = ref<GraphModel | null>(null);
const operandKeysByIndex = ref<string[]>([]);

const subjectAnchorGraph = computed<GraphModel>(() => {
    if (!modelValue.subject.graph_slug) {
        return anchorGraph;
    }
    const graphAtFirstSubjectSlug = graphs.value.find((graphModel) => {
        return graphModel.slug === modelValue.subject.graph_slug;
    });
    if (graphAtFirstSubjectSlug) {
        return graphAtFirstSubjectSlug;
    }
    return anchorGraph;
});

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
    if (!subjectNode.value?.datatype) {
        return [];
    }
    const facetsForDatatype =
        datatypesToAdvancedSearchFacets.value[subjectNode.value.datatype];
    if (!facetsForDatatype) {
        return [];
    }
    return facetsForDatatype;
});

const selectedAdvancedSearchFacet = computed<AdvancedSearchFacet | null>(() => {
    if (!modelValue.operator) {
        return null;
    }
    const matchingFacet = availableOperatorOptions.value.find((searchFacet) => {
        return searchFacet.operator === modelValue.operator;
    });
    return matchingFacet ?? null;
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
        const graphMatchingTerminalSlug = graphs.value.find((graphModel) => {
            return graphModel.slug === terminalGraphSlug;
        });

        if (!graphMatchingTerminalSlug) {
            return;
        }

        subjectGraph.value = graphMatchingTerminalSlug;

        const allNodesForGraph = await getNodesForGraphId(
            graphMatchingTerminalSlug.graphid,
        );
        const nodeMatchingTerminalAlias = allNodesForGraph.find((graphNode) => {
            return graphNode.alias === terminalNodeAlias;
        });

        subjectNode.value = nodeMatchingTerminalAlias ?? null;
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

function patchClause(partialClause: Partial<ClausePayload>): void {
    const updatedClause: ClausePayload = { ...modelValue, ...partialClause };
    emit("update:modelValue", updatedClause);
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
    updatedOperand: OperandPayload | null,
): void {
    const updatedOperands = [...modelValue.operands];
    if (updatedOperand === null) {
        updatedOperands[parameterIndex] = {
            type: OPERAND_TYPE_LITERAL,
            value: null,
        };
    } else {
        updatedOperands[parameterIndex] = updatedOperand;
    }
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
    const nextSearchFacet = availableOperatorOptions.value.find(
        (searchFacet) => {
            return searchFacet.operator === nextOperator;
        },
    );
    const nextFacetArity = nextSearchFacet?.arity ?? 0;
    if (previousFacetArity !== nextFacetArity) {
        patchClause({ operator: nextOperator, operands: [] });
        return;
    }
    patchClause({ operator: nextOperator });
}

function handleQuantifierChange(
    nextQuantifier: ClausePayload["quantifier"],
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
                <span
                    v-else
                    class="clause-subject-path clause-subject-all-text"
                >
                    {{ $gettext("All text nodes") }}
                </span>

                <Select
                    v-if="subjectNode?.nodegroup_has_cardinality_n"
                    :model-value="modelValue.quantifier"
                    class="clause-quantifier-select"
                    :options="clauseQuantifierOptions"
                    option-label="label"
                    option-value="value"
                    @update:model-value="handleQuantifierChange"
                />

                <Select
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
                        modelValue.subject.type ===
                            ClauseSubjectTypeToken.SEARCH_MODELS &&
                        selectedAdvancedSearchFacet &&
                        selectedAdvancedSearchFacet.arity > 0
                    "
                    class="clause-operands-row"
                >
                    <InputText
                        v-for="parameterIndex in selectedAdvancedSearchFacet.arity"
                        :key="ensureOperandKey(parameterIndex - 1)"
                        :model-value="
                            (modelValue.operands[parameterIndex - 1]
                                ?.value as string) ?? ''
                        "
                        :placeholder="$gettext('Search text...')"
                        @update:model-value="
                            handleOperandUpdate(parameterIndex - 1, {
                                type: OPERAND_TYPE_LITERAL,
                                value: $event,
                            })
                        "
                    />
                </div>
                <div
                    v-else-if="
                        selectedAdvancedSearchFacet &&
                        selectedAdvancedSearchFacet.arity > 0 &&
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
                            handleOperandUpdate(parameterIndex - 1, $event)
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
    margin-top: 1rem;
    font-size: 1rem;
    line-height: 1.25;
    opacity: 0.75;
}

.clause-remove-button {
    grid-column: 3;
    justify-self: flex-end;
}
</style>
