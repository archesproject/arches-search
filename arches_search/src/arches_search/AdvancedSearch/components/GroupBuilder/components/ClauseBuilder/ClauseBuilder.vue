<script setup lang="ts">
import { computed, inject, ref, watch, useId } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Button from "primevue/button";

import PathBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/PathBuilder.vue";
import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";

import type { Ref } from "vue";
import type {
    GraphModel,
    AdvancedSearchFacet,
    GroupPayload,
    Node,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type ClauseTypeToken = "LITERAL" | "RELATED";
type ClauseQuantifierToken = "ANY" | "ALL" | "NONE";
type OperandPayloadTypeToken = "LITERAL" | "PATH";

type OperandPayload = {
    type: OperandPayloadTypeToken;
    value: unknown;
};

type ClausePayload = {
    type: ClauseTypeToken;
    quantifier: ClauseQuantifierToken;
    subject: [string, string][];
    operator: string | null;
    operands: OperandPayload[];
};

type RelationshipPayload = GroupPayload["relationship"];

type NodeWithCardinality = Node & {
    nodegroup_has_cardinality_n?: boolean;
};

const CLAUSE_TYPE_RELATED: ClauseTypeToken = "RELATED";

const CLAUSE_QUANTIFIER_ANY: ClauseQuantifierToken = "ANY";
const CLAUSE_QUANTIFIER_ALL: ClauseQuantifierToken = "ALL";
const CLAUSE_QUANTIFIER_NONE: ClauseQuantifierToken = "NONE";

const OPERAND_TYPE_LITERAL: OperandPayloadTypeToken = "LITERAL";

const operandTypeLiteral: OperandPayloadTypeToken = OPERAND_TYPE_LITERAL;

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;

const getNodesForGraphId =
    inject<(graphId: string) => Promise<NodeWithCardinality[]>>(
        "getNodesForGraphId",
    )!;

const { modelValue, anchorGraph, relationship, innerGroupGraphSlug } =
    defineProps<{
        modelValue: ClausePayload;
        anchorGraph: GraphModel;
        relationship?: RelationshipPayload | null;
        innerGroupGraphSlug?: string;
    }>();

const emit = defineEmits<{
    (event: "update:modelValue", updatedClause: ClausePayload): void;
    (event: "request:remove"): void;
}>();

const clauseQuantifierOptions: {
    label: string;
    value: ClauseQuantifierToken;
}[] = [
    { label: $gettext("At least one"), value: CLAUSE_QUANTIFIER_ANY },
    { label: $gettext("Every"), value: CLAUSE_QUANTIFIER_ALL },
    { label: $gettext("No"), value: CLAUSE_QUANTIFIER_NONE },
];

const subjectNode = ref<NodeWithCardinality | null>(null);
const subjectGraph = ref<GraphModel | null>(null);
const operandKeysByIndex = ref<string[]>([]);

const subjectPath = computed<[string, string][]>(() => {
    return modelValue.subject;
});

const subjectPathTerminalGraphSlugAndNodeAlias = computed<
    [string, string] | null
>(() => {
    if (subjectPath.value.length === 0) {
        return null;
    }
    const lastIndex = subjectPath.value.length - 1;
    return subjectPath.value[lastIndex];
});

const baseSubjectAnchorGraph = computed<GraphModel>(() => {
    if (subjectPath.value.length === 0) {
        return anchorGraph;
    }

    const [firstGraphSlug] = subjectPath.value[0];

    const matchingGraph = graphs.value.find((graphCandidate) => {
        return graphCandidate.slug === firstGraphSlug;
    });

    if (matchingGraph) {
        return matchingGraph;
    }

    return anchorGraph;
});

const subjectAnchorGraph = computed<GraphModel>(() => {
    const isRelatedClause = modelValue.type === CLAUSE_TYPE_RELATED;

    if (
        subjectPath.value.length === 0 &&
        isRelatedClause &&
        relationship &&
        innerGroupGraphSlug
    ) {
        const isInverse = Boolean(relationship.is_inverse);
        const startingSlug = isInverse ? innerGroupGraphSlug : anchorGraph.slug;

        const matchingGraph = graphs.value.find((graphCandidate) => {
            return graphCandidate.slug === startingSlug;
        });

        if (matchingGraph) {
            return matchingGraph;
        }

        return anchorGraph;
    }

    return baseSubjectAnchorGraph.value;
});

const availableOperatorOptions = computed<AdvancedSearchFacet[]>(() => {
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

    const matchingFacet = availableOperatorOptions.value.find(
        (advancedSearchFacet) => {
            return advancedSearchFacet.operator === modelValue.operator;
        },
    );

    return matchingFacet ?? null;
});

const resolvedClauseQuantifierOptions = computed(() => {
    if (!subjectNode.value) {
        return clauseQuantifierOptions;
    }

    if (!subjectNode.value.nodegroup_has_cardinality_n) {
        return [
            {
                label: $gettext("Value of"),
                value: CLAUSE_QUANTIFIER_ANY,
            },
        ];
    }

    return clauseQuantifierOptions;
});

watch(
    subjectPathTerminalGraphSlugAndNodeAlias,
    async (updatedTerminal) => {
        subjectNode.value = null;
        subjectGraph.value = null;

        if (!updatedTerminal) {
            return;
        }

        const [terminalGraphSlug, terminalNodeAlias] = updatedTerminal;

        const matchingGraph = graphs.value.find((graphCandidate) => {
            return graphCandidate.slug === terminalGraphSlug;
        });

        if (!matchingGraph) {
            return;
        }

        const allNodesForGraph = await getNodesForGraphId(
            matchingGraph.graphid,
        );

        subjectGraph.value = matchingGraph;
        subjectNode.value =
            allNodesForGraph.find((nodeCandidate) => {
                return nodeCandidate.alias === terminalNodeAlias;
            }) ?? null;
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
    const updatedClause: ClausePayload = {
        ...modelValue,
        ...partialClause,
    };
    emit("update:modelValue", updatedClause);
}

function ensureOperandKey(parameterIndex: number): string {
    if (!operandKeysByIndex.value[parameterIndex]) {
        operandKeysByIndex.value[parameterIndex] = useId();
    }
    return operandKeysByIndex.value[parameterIndex];
}

function handleSubjectUpdate(
    updatedSubjectPathSequence: [string, string][],
): void {
    patchClause({
        subject: updatedSubjectPathSequence,
        operator: null,
        operands: [],
    });
}

function handleOperandUpdate(
    parameterIndex: number,
    updatedOperand: OperandPayload | null,
): void {
    const currentOperands = modelValue.operands ?? [];
    const updatedOperands = [...currentOperands];

    if (updatedOperand === null) {
        updatedOperands[parameterIndex] = {
            type: operandTypeLiteral,
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
        patchClause({
            operator: null,
            operands: [],
        });
        return;
    }

    const previousFacet =
        availableOperatorOptions.value.find((advancedSearchFacet) => {
            return advancedSearchFacet.operator === modelValue.operator;
        }) ?? null;

    const nextFacet =
        availableOperatorOptions.value.find((advancedSearchFacet) => {
            return advancedSearchFacet.operator === nextOperator;
        }) ?? null;

    const previousArity = previousFacet ? previousFacet.arity : 0;
    const nextArity = nextFacet ? nextFacet.arity : 0;

    if (previousArity !== nextArity) {
        patchClause({
            operator: nextOperator,
            operands: [],
        });

        return;
    }

    patchClause({
        operator: nextOperator,
    });
}

function handleRemoveSelf(): void {
    emit("request:remove");
}

function handleQuantifierClick(nextQuantifier: ClauseQuantifierToken): void {
    if (modelValue.quantifier === nextQuantifier) {
        return;
    }
    patchClause({ quantifier: nextQuantifier });
}
</script>

<template>
    <div class="clause-builder">
        <div class="clause-core-row">
            <Select
                :disabled="!subjectNode?.nodegroup_has_cardinality_n"
                :model-value="modelValue.quantifier"
                class="clause-quantifier-select"
                :options="resolvedClauseQuantifierOptions"
                option-label="label"
                option-value="value"
                @update:model-value="handleQuantifierClick"
            />

            <PathBuilder
                class="clause-subject-path"
                :path-sequence="subjectPath"
                :graph-slugs="[subjectAnchorGraph.slug]"
                @update:path-sequence="handleSubjectUpdate"
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
                    :operand-type="operandTypeLiteral"
                    @update:model-value="
                        handleOperandUpdate(parameterIndex - 1, $event)
                    "
                />
            </div>
        </div>

        <Button
            class="clause-remove-button"
            icon="pi pi-times"
            severity="danger"
            variant="text"
            type="button"
            :aria-label="$gettext('Remove filter')"
            @click="handleRemoveSelf"
        />
    </div>
</template>

<style scoped>
:deep(.clause-indicator-pill .p-tag-icon) {
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
    margin-inline-end: 1rem;
}

.clause-builder {
    font-size: 1rem;
    gap: 0.5rem;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: flex-start;
}

.clause-gear-toggle {
    margin-top: 0.15rem;
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

.clause-indicator-pill {
    padding: 0.5rem 1rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.clause-advanced-row {
    margin-top: 0.5rem;
    margin-inline-start: 2.75rem;
}

.clause-remove-button {
    justify-self: flex-end;
}
</style>
