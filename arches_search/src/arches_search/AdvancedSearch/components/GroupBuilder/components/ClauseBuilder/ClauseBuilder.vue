<script setup lang="ts">
import {
    computed,
    defineEmits,
    defineProps,
    inject,
    ref,
    watch,
    useId,
} from "vue";
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
    Node,
    GroupPayload,
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
    slug?: string;
    graphid?: string;
    [key: string]: unknown;
};

type RelationshipPayload = GroupPayload["relationship"];

const props = defineProps<{
    modelValue: ClausePayload;
    anchorGraph: GraphSummary;
    parentGroupAnchorGraph?: GraphSummary;
    relationship?: RelationshipPayload | null;
    innerGroupGraphSlug?: string;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", updatedClause: ClausePayload): void;
    (event: "request:remove"): void;
}>();

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;
const graphs = inject<Ref<GraphSummary[]>>("graphs")!;
const getNodesForGraphId =
    inject<(graphId: string) => Promise<Node[]>>("getNodesForGraphId")!;

const clauseTypeOptions: { label: string; value: ClauseTypeToken }[] = [
    { label: $gettext("Literal value"), value: "LITERAL" },
    { label: $gettext("Related resource"), value: "RELATED" },
];

const clauseQuantifierOptions: {
    label: string;
    value: ClauseQuantifierToken;
}[] = [
    { label: $gettext("Any"), value: "ANY" },
    { label: $gettext("All"), value: "ALL" },
    { label: $gettext("None"), value: "NONE" },
];

const operandTypeOptions: {
    label: string;
    value: OperandPayloadTypeToken;
}[] = [
    { label: $gettext("Literal"), value: "LITERAL" },
    { label: $gettext("Path"), value: "PATH" },
];

const isAdvancedOptionsOpen = ref(false);

const localClauseType = ref<ClauseTypeToken>(props.modelValue.type);
const localQuantifier = ref<ClauseQuantifierToken>(props.modelValue.quantifier);
const localOperator = ref<string | null>(props.modelValue.operator);

const initialOperandType: OperandPayloadTypeToken =
    props.modelValue.operands &&
    props.modelValue.operands.length > 0 &&
    props.modelValue.operands[0]?.type === "PATH"
        ? "PATH"
        : "LITERAL";

const localOperandType = ref<OperandPayloadTypeToken>(initialOperandType);

const subjectTerminalNode = ref<Node | null>(null);
const subjectTerminalGraph = ref<GraphSummary | null>(null);
const operandKeysByIndex = ref<string[]>([]);

const subjectPathSequence = computed<[string, string][]>(() => {
    return props.modelValue.subject ?? [];
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
    return subjectPathSequence.value[subjectPathSequence.value.length - 1];
});

const baseSubjectAnchorGraph = computed<GraphSummary>(() => {
    if (subjectPathSequence.value.length > 0) {
        const [firstGraphSlug] = subjectPathSequence.value[0];
        if (firstGraphSlug) {
            const matchingGraph = graphs.value.find((graphCandidate) => {
                return graphCandidate.slug === firstGraphSlug;
            });
            if (matchingGraph) {
                return matchingGraph;
            }
            return { slug: firstGraphSlug };
        }
    }
    return props.anchorGraph;
});

const subjectAnchorGraph = computed<GraphSummary>(() => {
    if (
        subjectPathSequence.value.length === 0 &&
        props.modelValue.type === "RELATED" &&
        props.relationship &&
        props.innerGroupGraphSlug
    ) {
        const isInverse = Boolean(props.relationship.is_inverse);
        const startingSlug = isInverse
            ? props.innerGroupGraphSlug
            : props.anchorGraph.slug;

        const matchingGraph = graphs.value.find((graphCandidate) => {
            return graphCandidate.slug === startingSlug;
        });

        return matchingGraph ?? { slug: startingSlug };
    }

    return baseSubjectAnchorGraph.value;
});

const operandAnchorGraph = computed<GraphSummary>(() => {
    if (
        props.modelValue.type === "RELATED" &&
        props.relationship &&
        props.innerGroupGraphSlug
    ) {
        const isInverse = Boolean(props.relationship.is_inverse);
        const oppositeSlug = isInverse
            ? props.anchorGraph.slug
            : props.innerGroupGraphSlug;

        const matchingGraph = graphs.value.find((graphCandidate) => {
            return graphCandidate.slug === oppositeSlug;
        });

        return matchingGraph ?? { slug: oppositeSlug };
    }

    return props.anchorGraph;
});

const availableOperatorOptions = computed<AdvancedSearchFacet[]>(() => {
    if (!subjectTerminalNode.value?.datatype) {
        return [];
    }
    const facetsForDatatype =
        datatypesToAdvancedSearchFacets.value[
            subjectTerminalNode.value.datatype
        ] ?? [];
    return facetsForDatatype;
});

const selectedAdvancedSearchFacet = computed<AdvancedSearchFacet | null>(() => {
    if (!localOperator.value) {
        return null;
    }
    const matchingFacet = availableOperatorOptions.value.find(
        (advancedSearchFacet) => {
            return advancedSearchFacet.operator === localOperator.value;
        },
    );
    return matchingFacet ?? null;
});

watch(
    () => props.modelValue,
    (updatedClause) => {
        if (localClauseType.value !== updatedClause.type) {
            localClauseType.value = updatedClause.type;
        }
        if (localQuantifier.value !== updatedClause.quantifier) {
            localQuantifier.value = updatedClause.quantifier;
        }
        if (localOperator.value !== updatedClause.operator) {
            localOperator.value = updatedClause.operator;
        }
        if (
            updatedClause.operands &&
            updatedClause.operands.length > 0 &&
            updatedClause.operands[0]?.type &&
            updatedClause.operands[0].type !== localOperandType.value
        ) {
            localOperandType.value = updatedClause.operands[0]
                .type as OperandPayloadTypeToken;
        }
    },
    { deep: true },
);

watch(
    subjectPathTerminalGraphSlugAndNodeAlias,
    async (updatedTerminal) => {
        subjectTerminalNode.value = null;
        subjectTerminalGraph.value = null;

        if (!updatedTerminal) {
            return;
        }

        const [terminalGraphSlug, terminalNodeAlias] = updatedTerminal;
        if (!terminalGraphSlug || !terminalNodeAlias) {
            return;
        }

        const matchingGraph = graphs.value.find((graphCandidate) => {
            return graphCandidate.slug === terminalGraphSlug;
        });

        if (!matchingGraph || !matchingGraph.graphid) {
            return;
        }

        const allNodesForGraph = await getNodesForGraphId(
            matchingGraph.graphid as string,
        );

        subjectTerminalGraph.value = matchingGraph;
        subjectTerminalNode.value =
            allNodesForGraph.find((nodeCandidate) => {
                return nodeCandidate.alias === terminalNodeAlias;
            }) ?? null;
    },
    { immediate: true },
);

watch(localOperator, (updatedOperator, previousOperator) => {
    if (updatedOperator === previousOperator) {
        return;
    }
    patchClause({ operator: updatedOperator, operands: [] });
});

watch(localClauseType, (updatedType, previousType) => {
    if (updatedType === previousType) {
        return;
    }

    const resetClause: ClausePayload = {
        ...props.modelValue,
        type: updatedType,
        quantifier: "ANY",
        subject: [],
        operator: null,
        operands: [],
    };

    emit("update:modelValue", resetClause);
    localQuantifier.value = resetClause.quantifier;
    localOperator.value = resetClause.operator;
});

watch(localQuantifier, (updatedQuantifier, previousQuantifier) => {
    if (updatedQuantifier === previousQuantifier) {
        return;
    }
    patchClause({ quantifier: updatedQuantifier });
});

function patchClause(partialClause: Partial<ClausePayload>): void {
    const updatedClause: ClausePayload = {
        ...props.modelValue,
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
    if (
        updatedSubjectPathSequence === props.modelValue.subject ||
        JSON.stringify(updatedSubjectPathSequence) ===
            JSON.stringify(props.modelValue.subject)
    ) {
        return;
    }
    patchClause({
        subject: updatedSubjectPathSequence,
        operator: null,
        operands: [],
    });
    localOperator.value = null;
}

function handleOperandUpdate(
    parameterIndex: number,
    updatedOperand: OperandPayload | null,
): void {
    const currentOperands = props.modelValue.operands ?? [];
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

function handleRemoveSelf(): void {
    emit("request:remove");
}

function handleToggleAdvancedOptions(event: MouseEvent): void {
    event.stopPropagation();
    isAdvancedOptionsOpen.value = !isAdvancedOptionsOpen.value;
}

function handleRelationshipTypeClick(
    nextRelationshipType: ClauseTypeToken,
): void {
    if (localClauseType.value === nextRelationshipType) {
        return;
    }
    localClauseType.value = nextRelationshipType;
}

function handleQuantifierClick(nextQuantifier: ClauseQuantifierToken): void {
    if (localQuantifier.value === nextQuantifier) {
        return;
    }
    localQuantifier.value = nextQuantifier;
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
            <Button
                class="clause-gear-toggle"
                icon="pi pi-cog"
                severity="secondary"
                text
                rounded
                type="button"
                :aria-label="$gettext('Toggle advanced clause options')"
                :aria-pressed="isAdvancedOptionsOpen"
                @click="handleToggleAdvancedOptions"
            />

            <div class="clause-core-row">
                <PathBuilder
                    :key="subjectPathSequenceKey"
                    class="clause-subject-path"
                    :path-sequence="subjectPathSequence"
                    :anchor-graph="subjectAnchorGraph"
                    :show-anchor-graph-dropdown="
                        props.modelValue.type === 'RELATED'
                    "
                    @update:path-sequence="handleSubjectUpdate"
                />

                <Select
                    v-model="localOperator"
                    class="clause-operator-select"
                    :options="availableOperatorOptions"
                    option-label="label"
                    option-value="operator"
                    :disabled="availableOperatorOptions.length === 0"
                    :placeholder="$gettext('Select an operator...')"
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
                            modelValue.operands?.[parameterIndex - 1] ?? null
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
                    v-if="localClauseType === 'RELATED'"
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
                @click="handleRemoveSelf"
            />
        </div>

        <div
            v-if="isAdvancedOptionsOpen"
            class="clause-advanced-row"
        >
            <ClauseAdvancedOptions
                :clause-type="localClauseType"
                :quantifier="localQuantifier"
                :operand-type="localOperandType"
                :clause-type-options="clauseTypeOptions"
                :clause-quantifier-options="clauseQuantifierOptions"
                :operand-type-options="operandTypeOptions"
                @update:clause-type="handleRelationshipTypeClick"
                @update:quantifier="handleQuantifierClick"
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
    flex-shrink: 0;
    margin-top: 0.15rem;
}

.clause-core-row {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.clause-subject-path {
}

.clause-operator-select {
    flex: 0 0 14rem;
    min-width: 10rem;
}

.clause-operands-row {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    flex: 1 1 auto;
    flex-wrap: wrap;
}

.clause-indicator-pill {
    padding: 0.5rem 1rem;
    font-size: 1.2rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.clause-remove-button {
    flex-shrink: 0;
}

.clause-advanced-row {
    margin-top: 0.5rem;
    margin-inline-start: 2.75rem;
}
</style>
