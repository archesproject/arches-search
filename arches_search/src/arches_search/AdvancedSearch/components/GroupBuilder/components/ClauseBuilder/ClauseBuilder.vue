<script setup lang="ts">
import { computed, inject, ref, watch, useId } from "vue";
import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Button from "primevue/button";
import Tag from "primevue/tag";

import PathBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/PathBuilder.vue";
import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";
import ClauseAdvancedOptions from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/ClauseBuilder/components/ClauseAdvancedOptions.vue";

import type { Ref } from "vue";
import type {
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

type GraphSummary = {
    graphid: string;
    slug: string;
    name: string;
    [key: string]: unknown;
};

type RelationshipPayload = GroupPayload["relationship"];

const CLAUSE_TYPE_LITERAL: ClauseTypeToken = "LITERAL";
const CLAUSE_TYPE_RELATED: ClauseTypeToken = "RELATED";

const CLAUSE_QUANTIFIER_ANY: ClauseQuantifierToken = "ANY";
const CLAUSE_QUANTIFIER_ALL: ClauseQuantifierToken = "ALL";
const CLAUSE_QUANTIFIER_NONE: ClauseQuantifierToken = "NONE";

const OPERAND_TYPE_LITERAL: OperandPayloadTypeToken = "LITERAL";
const OPERAND_TYPE_PATH: OperandPayloadTypeToken = "PATH";

const clauseTypeOptions: { label: string; value: ClauseTypeToken }[] = [
    { label: $gettext("Literal value"), value: CLAUSE_TYPE_LITERAL },
    { label: $gettext("Related resource"), value: CLAUSE_TYPE_RELATED },
];

const clauseQuantifierOptions: {
    label: string;
    value: ClauseQuantifierToken;
}[] = [
    { label: $gettext("Any"), value: CLAUSE_QUANTIFIER_ANY },
    { label: $gettext("All"), value: CLAUSE_QUANTIFIER_ALL },
    { label: $gettext("No"), value: CLAUSE_QUANTIFIER_NONE },
];

const operandTypeOptions: {
    label: string;
    value: OperandPayloadTypeToken;
}[] = [
    { label: $gettext("Literal"), value: OPERAND_TYPE_LITERAL },
    { label: $gettext("Path"), value: OPERAND_TYPE_PATH },
];

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets");

if (!datatypesToAdvancedSearchFacets) {
    throw new Error(
        $gettext(
            "ClauseBuilder is missing datatypesToAdvancedSearchFacets injection.",
        ),
    );
}

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

if (!graphs) {
    throw new Error($gettext("ClauseBuilder is missing graphs injection."));
}

const getNodesForGraphId =
    inject<(graphId: string) => Promise<Node[]>>("getNodesForGraphId");

if (!getNodesForGraphId) {
    throw new Error(
        $gettext("ClauseBuilder is missing getNodesForGraphId injection."),
    );
}

const emit = defineEmits<{
    (event: "update:modelValue", updatedClause: ClausePayload): void;
    (event: "request:remove"): void;
}>();

const {
    modelValue,
    anchorGraph,
    parentGroupAnchorGraph,
    relationship,
    innerGroupGraphSlug,
} = defineProps<{
    modelValue: ClausePayload;
    anchorGraph: GraphSummary;
    parentGroupAnchorGraph?: GraphSummary;
    relationship?: RelationshipPayload | null;
    innerGroupGraphSlug?: string;
}>();

const isAdvancedOptionsOpen = ref(false);
const subjectTerminalNode = ref<Node | null>(null);
const subjectTerminalGraph = ref<GraphSummary | null>(null);
const operandKeysByIndex = ref<string[]>([]);
const localOperandType = ref<OperandPayloadTypeToken>(OPERAND_TYPE_LITERAL);

if (modelValue.operands[0]?.type === OPERAND_TYPE_PATH) {
    localOperandType.value = OPERAND_TYPE_PATH;
}

const subjectPathSequence = computed<[string, string][]>(() => {
    return modelValue.subject;
});

const subjectPathSequenceKey = computed<string>(() => {
    return subjectPathSequence.value
        .map(([graphSlug, nodeAlias]) => `${graphSlug}:${nodeAlias}`)
        .join("|");
});

const subjectPathTerminalGraphSlugAndNodeAlias = computed<
    [string, string] | null
>(() => {
    if (subjectPathSequence.value.length === 0) {
        return null;
    }
    const lastIndex = subjectPathSequence.value.length - 1;
    return subjectPathSequence.value[lastIndex];
});

const baseSubjectAnchorGraph = computed<GraphSummary>(() => {
    if (subjectPathSequence.value.length === 0) {
        return anchorGraph;
    }

    const [firstGraphSlug] = subjectPathSequence.value[0];

    const matchingGraph = graphs.value.find((graphCandidate) => {
        return graphCandidate.slug === firstGraphSlug;
    });

    if (matchingGraph) {
        return matchingGraph;
    }

    return anchorGraph;
});

const subjectAnchorGraph = computed<GraphSummary>(() => {
    const isRelatedClause = modelValue.type === CLAUSE_TYPE_RELATED;

    if (
        subjectPathSequence.value.length === 0 &&
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

const operandAnchorGraph = computed<GraphSummary>(() => {
    const isRelatedClause = modelValue.type === CLAUSE_TYPE_RELATED;

    if (isRelatedClause && relationship && innerGroupGraphSlug) {
        const isInverse = Boolean(relationship.is_inverse);
        const oppositeSlug = isInverse ? anchorGraph.slug : innerGroupGraphSlug;

        const matchingGraph = graphs.value.find((graphCandidate) => {
            return graphCandidate.slug === oppositeSlug;
        });

        if (matchingGraph) {
            return matchingGraph;
        }

        return anchorGraph;
    }

    return anchorGraph;
});

const availableOperatorOptions = computed<AdvancedSearchFacet[]>(() => {
    if (!subjectTerminalNode.value?.datatype) {
        return [];
    }

    const facetsForDatatype =
        datatypesToAdvancedSearchFacets.value[
            subjectTerminalNode.value.datatype
        ];

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

    if (!matchingFacet) {
        return null;
    }

    return matchingFacet;
});

watch(
    subjectPathTerminalGraphSlugAndNodeAlias,
    async (updatedTerminal) => {
        subjectTerminalNode.value = null;
        subjectTerminalGraph.value = null;

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

        subjectTerminalGraph.value = matchingGraph;
        subjectTerminalNode.value =
            allNodesForGraph.find((nodeCandidate) => {
                return nodeCandidate.alias === terminalNodeAlias;
            }) ?? null;
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
            type: localOperandType.value,
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

// function handleToggleAdvancedOptions(event: MouseEvent): void {
//     event.stopPropagation();
//     isAdvancedOptionsOpen.value = !isAdvancedOptionsOpen.value;
// }

function handleClauseTypeClick(nextClauseType: ClauseTypeToken): void {
    if (modelValue.type === nextClauseType) {
        return;
    }

    patchClause({
        type: nextClauseType,
        quantifier: CLAUSE_QUANTIFIER_ANY,
        subject: [],
        operator: null,
        operands: [],
    });
}

function handleQuantifierClick(nextQuantifier: ClauseQuantifierToken): void {
    if (modelValue.quantifier === nextQuantifier) {
        return;
    }
    patchClause({ quantifier: nextQuantifier });
}

function handleOperandTypeClick(
    nextOperandType: OperandPayloadTypeToken,
): void {
    if (localOperandType.value === nextOperandType) {
        return;
    }
    localOperandType.value = nextOperandType;
}
</script>

<template>
    <div class="clause-builder">
        <div class="clause-main-row">
            <!-- <Button
                class="clause-gear-toggle"
                icon="pi pi-cog"
                severity="secondary"
                text
                rounded
                type="button"
                :aria-label="$gettext('Toggle advanced options')"
                :aria-pressed="isAdvancedOptionsOpen"
                @click="handleToggleAdvancedOptions"
            /> -->

            <div class="clause-core-row">
                <Select
                    :model-value="modelValue.quantifier"
                    class="clause-quantifier-select"
                    :options="clauseQuantifierOptions"
                    option-label="label"
                    option-value="value"
                    @update:model-value="handleQuantifierClick"
                />

                <PathBuilder
                    :key="subjectPathSequenceKey"
                    class="clause-subject-path"
                    :path-sequence="subjectPathSequence"
                    :anchor-graph="subjectAnchorGraph"
                    :show-anchor-graph-dropdown="
                        modelValue.type === CLAUSE_TYPE_RELATED
                    "
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
                        subjectTerminalNode &&
                        subjectTerminalGraph
                    "
                    class="clause-operands-row"
                >
                    <ClauseOperandBuilder
                        v-for="parameterIndex in selectedAdvancedSearchFacet.arity"
                        :key="ensureOperandKey(parameterIndex - 1)"
                        :model-value="
                            modelValue.operands[parameterIndex - 1] ?? null
                        "
                        :anchor-graph="operandAnchorGraph"
                        :parent-group-anchor-graph="parentGroupAnchorGraph"
                        :subject-terminal-node="subjectTerminalNode"
                        :subject-terminal-graph="subjectTerminalGraph"
                        :operand-type="localOperandType"
                        @update:model-value="
                            handleOperandUpdate(parameterIndex - 1, $event)
                        "
                    />
                </div>

                <Tag
                    v-if="modelValue.type === CLAUSE_TYPE_RELATED"
                    class="clause-indicator-pill"
                    icon="pi pi-link"
                    :value="$gettext('Related')"
                />
            </div>

            <Button
                icon="pi pi-times"
                severity="danger"
                type="button"
                class="clause-remove-button"
                :aria-label="$gettext('Remove filter')"
                @click="handleRemoveSelf"
            />
        </div>

        <div
            v-if="isAdvancedOptionsOpen"
            class="clause-advanced-row"
        >
            <ClauseAdvancedOptions
                :clause-type="modelValue.type"
                :operand-type="localOperandType"
                :clause-type-options="clauseTypeOptions"
                :operand-type-options="operandTypeOptions"
                @update:clause-type="handleClauseTypeClick"
                @update:operand-type="handleOperandTypeClick"
            />
        </div>
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
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.clause-main-row {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: flex-start;
    column-gap: 0.5rem;
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
