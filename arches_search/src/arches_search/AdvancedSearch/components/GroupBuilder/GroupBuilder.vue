<script setup lang="ts">
import {
    defineProps,
    defineEmits,
    ref,
    computed,
    watchEffect,
    defineOptions,
    inject,
} from "vue";
import Card from "primevue/card";

import {
    GraphScopeToken,
    LogicToken,
    type GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

import {
    makeEmptyGroupPayload,
    setGraphSlug,
    setScope,
    toggleLogic,
    removeChildGroupAtIndex,
    addEmptyLiteralClauseToGroup,
    removeClauseAtIndex as removeClauseAtIndexFromPayload,
    addRelationshipIfMissing,
    clearRelationshipIfPresent,
    reconcileStableKeys,
} from "@/arches_search/AdvancedSearch/advanced-search-payload-builder.ts";

import GroupBracket from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/GroupBracket.vue";
import GroupHeader from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/GroupHeader/GroupHeader.vue";
import ClauseBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/ClauseBuilder/ClauseBuilder.vue";

defineOptions({ name: "GroupBuilder" });

type GraphSummary = {
    id?: string;
    graphid?: string;
    slug?: string;
    [key: string]: unknown;
};

type ClausePayload = GroupPayload["clauses"][number];

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

const emit = defineEmits<{
    (event: "update:modelValue", value: GroupPayload): void;
    (event: "remove"): void;
}>();

const props = defineProps<{
    modelValue?: GroupPayload;
    isRoot?: boolean;
    parentGroupAnchorGraph?: GraphSummary;
}>();

const currentGroup = computed<GroupPayload>(function getCurrentGroup() {
    return props.modelValue ?? makeEmptyGroupPayload();
});

const currentGroupAnchorGraph = computed<GraphSummary | null>(
    function getCurrentGroupAnchorGraph() {
        const allGraphs = graphs?.value ?? [];
        const groupSlug = currentGroup.value.graph_slug;
        if (!groupSlug) {
            return null;
        }
        return (
            allGraphs.find(function findMatchingGraph(candidateGraph) {
                return candidateGraph.slug === groupSlug;
            }) ?? null
        );
    },
);

const effectiveAnchorGraph = computed<GraphSummary>(
    function getEffectiveAnchorGraph() {
        if (currentGroupAnchorGraph.value) {
            return currentGroupAnchorGraph.value;
        }
        if (props.parentGroupAnchorGraph) {
            return props.parentGroupAnchorGraph;
        }
        return { slug: currentGroup.value.graph_slug };
    },
);

const childGroupKeys = ref<string[]>([]);
const clauseKeys = ref<string[]>([]);

const hasBracket = computed<boolean>(function getHasBracket() {
    return (
        currentGroup.value.groups.length + currentGroup.value.clauses.length >=
        2
    );
});

const hasBodyContent = computed<boolean>(function getHasBodyContent() {
    return (
        currentGroup.value.clauses.length > 0 ||
        currentGroup.value.groups.length > 0
    );
});

watchEffect(function reconcileKeys() {
    childGroupKeys.value = reconcileStableKeys(
        childGroupKeys.value,
        currentGroup.value.groups.length,
        createId,
    );

    clauseKeys.value = reconcileStableKeys(
        clauseKeys.value,
        currentGroup.value.clauses.length,
        createId,
    );
});

function createId(): string {
    return crypto.randomUUID();
}

function commit(nextGroup: GroupPayload): void {
    emit("update:modelValue", nextGroup);
}

function onSetGraphSlug(graphSlug: string): void {
    const currentGraphSlug = currentGroup.value.graph_slug;

    const didGraphChange =
        Boolean(currentGraphSlug) && currentGraphSlug !== graphSlug;

    const updatedWithSlug = setGraphSlug(currentGroup.value, graphSlug);

    if (didGraphChange) {
        const clearedGroup: GroupPayload = {
            ...updatedWithSlug,
            clauses: [],
            groups: [],
            relationship: null,
        };
        commit(clearedGroup);
        return;
    }

    commit(updatedWithSlug);
}

function onSetScope(scopeToken: GraphScopeToken): void {
    commit(setScope(currentGroup.value, scopeToken));
}

function onSetLogicFromBracket(_: LogicToken): void {
    commit(toggleLogic(currentGroup.value));
}

function onAddGroup(): void {
    const updatedParent: GroupPayload = {
        ...currentGroup.value,
        groups: [...currentGroup.value.groups, makeEmptyGroupPayload()],
    };
    commit(updatedParent);
}

function onRemoveChildGroup(childIndex: number): void {
    const groupWithoutChild = removeChildGroupAtIndex(
        currentGroup.value,
        childIndex,
    );

    const hasAnyGroups = groupWithoutChild.groups.length > 0;
    const hasRelationship = groupWithoutChild.relationship !== null;

    let nextGroup: GroupPayload = groupWithoutChild;

    if (!hasAnyGroups && hasRelationship) {
        nextGroup = {
            ...groupWithoutChild,
            relationship: null,
            clauses: groupWithoutChild.clauses.filter(
                function keepLiteralClauses(clause) {
                    return clause.type === "LITERAL";
                },
            ),
        };
    }

    commit(nextGroup);
}

function onAddClause(): void {
    commit(addEmptyLiteralClauseToGroup(currentGroup.value));
}

function onUpdateClauseAtIndex(
    updatedClause: unknown,
    clauseIndex: number,
): void {
    const updatedClauses: ClausePayload[] = [...currentGroup.value.clauses];
    updatedClauses[clauseIndex] = updatedClause as ClausePayload;
    const updatedGroup: GroupPayload = {
        ...currentGroup.value,
        clauses: updatedClauses,
    };
    commit(updatedGroup);
}

function onRemoveClause(clauseIndex: number): void {
    commit(removeClauseAtIndexFromPayload(currentGroup.value, clauseIndex));
}

function onAddRelationship(): void {
    commit(addRelationshipIfMissing(currentGroup.value));
}

function onRemoveRelationship(): void {
    commit(clearRelationshipIfPresent(currentGroup.value));
}

function onUpdateChildGroupModelValue(
    updatedChildGroupPayload: GroupPayload,
    childIndex: number,
): void {
    const previousChildGroup = currentGroup.value.groups[childIndex];

    const previousChildGraphSlug = previousChildGroup?.graph_slug;
    const nextChildGraphSlug = updatedChildGroupPayload.graph_slug;

    const didChildGraphChange =
        Boolean(previousChildGraphSlug) &&
        Boolean(nextChildGraphSlug) &&
        previousChildGraphSlug !== nextChildGraphSlug;

    const updatedGroups = [...currentGroup.value.groups];
    updatedGroups[childIndex] = updatedChildGroupPayload;

    let updatedClauses: ClausePayload[] = [...currentGroup.value.clauses];
    let updatedRelationship = currentGroup.value.relationship;

    if (didChildGraphChange) {
        updatedClauses = updatedClauses.filter(
            function keepLiteralClauses(clause) {
                return clause.type === "LITERAL";
            },
        );

        if (childIndex === 0 && updatedRelationship !== null) {
            updatedRelationship = null;
        }
    }

    const updatedParent: GroupPayload = {
        ...currentGroup.value,
        groups: updatedGroups,
        clauses: updatedClauses,
        relationship: updatedRelationship,
    };

    commit(updatedParent);
}

function onUpdateRelationship(
    nextRelationship: GroupPayload["relationship"],
): void {
    if (nextRelationship === null) {
        const clearedRelationshipGroup: GroupPayload = {
            ...currentGroup.value,
            relationship: null,
            clauses: currentGroup.value.clauses.filter(
                function keepLiteralClauses(clause) {
                    return clause.type === "LITERAL";
                },
            ),
        };
        commit(clearedRelationshipGroup);
        return;
    }

    const previousRelationship = currentGroup.value.relationship;

    const didFlipDirection =
        previousRelationship !== null &&
        Boolean(previousRelationship.is_inverse) !==
            Boolean(nextRelationship.is_inverse);

    let updatedGroup: GroupPayload = {
        ...currentGroup.value,
        relationship: nextRelationship,
    };

    if (didFlipDirection) {
        updatedGroup = {
            ...updatedGroup,
            clauses: updatedGroup.clauses.filter(
                function keepLiteralClauses(clause) {
                    return clause.type === "LITERAL";
                },
            ),
        };
    }

    commit(updatedGroup);
}
</script>

<template>
    <Card class="group-card">
        <template #title>
            <GroupHeader
                :has-body-content="hasBodyContent"
                :graph-slug="currentGroup.graph_slug"
                :scope="currentGroup.scope"
                :is-root="Boolean(props.isRoot)"
                :has-relationship="Boolean(currentGroup.relationship !== null)"
                :relationship="currentGroup.relationship"
                :inner-graph-slug="currentGroup.groups[0]?.graph_slug"
                :has-nested-groups="currentGroup.groups.length > 0"
                @change-graph="onSetGraphSlug"
                @change-scope="onSetScope"
                @add-group="onAddGroup"
                @add-clause="onAddClause"
                @add-relationship="onAddRelationship"
                @remove-relationship="onRemoveRelationship"
                @update-relationship="onUpdateRelationship"
                @remove-group="$emit('remove')"
            />
        </template>

        <template #content>
            <div class="group-content">
                <div
                    :class="[
                        'group-grid',
                        hasBracket && 'group-grid-with-bracket',
                    ]"
                >
                    <GroupBracket
                        :show="hasBracket"
                        :logic="currentGroup.logic"
                        @update:logic="onSetLogicFromBracket"
                    />

                    <div class="group-body">
                        <div
                            v-if="currentGroup.clauses.length > 0"
                            :class="[
                                'clauses',
                                !hasBracket && 'clauses-without-bracket',
                            ]"
                        >
                            <Card
                                v-for="(
                                    clause, clauseIndex
                                ) in currentGroup.clauses"
                                :key="clauseKeys[clauseIndex]"
                                class="clause-card"
                            >
                                <template #content>
                                    <ClauseBuilder
                                        :model-value="clause as never"
                                        :anchor-graph="effectiveAnchorGraph"
                                        :parent-group-anchor-graph="
                                            props.parentGroupAnchorGraph
                                        "
                                        :relationship="
                                            currentGroup.relationship
                                        "
                                        :inner-group-graph-slug="
                                            currentGroup.groups[0]?.graph_slug
                                        "
                                        @update:model-value="
                                            onUpdateClauseAtIndex(
                                                $event,
                                                clauseIndex,
                                            )
                                        "
                                        @request:remove="
                                            onRemoveClause(clauseIndex)
                                        "
                                    />
                                </template>
                            </Card>
                        </div>

                        <div
                            v-if="currentGroup.groups.length > 0"
                            :class="[
                                'children',
                                !hasBracket && 'children-without-bracket',
                            ]"
                        >
                            <GroupBuilder
                                v-for="(
                                    childGroup, childIndex
                                ) in currentGroup.groups"
                                :key="childGroupKeys[childIndex]"
                                :model-value="childGroup"
                                :parent-group-anchor-graph="
                                    effectiveAnchorGraph
                                "
                                @update:model-value="
                                    onUpdateChildGroupModelValue(
                                        $event,
                                        childIndex,
                                    )
                                "
                                @remove="() => onRemoveChildGroup(childIndex)"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </template>
    </Card>
</template>

<style scoped>
.group {
    display: block;
    margin-bottom: 1rem;
}

.group-card {
    border: 0.0125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
}

.clause-card {
    border: 0.0125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
}

.group-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.group-grid {
    display: flex;
    align-items: stretch;
    width: 100%;
}

.group-grid-with-bracket {
    display: flex;
    align-items: stretch;
}

.group-grid-with-bracket :deep(.bracket) {
    flex: 0 0 4rem;
}

.group-body {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-width: 0;
}

.clauses {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.children {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.clauses-without-bracket,
.children-without-bracket {
    margin-inline-start: 4.25rem;
}
</style>
