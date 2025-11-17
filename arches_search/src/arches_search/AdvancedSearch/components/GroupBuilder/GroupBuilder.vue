<script setup lang="ts">
import { ref, computed, watchEffect, inject } from "vue";

import Card from "primevue/card";

import GroupBracket from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/GroupBracket.vue";
import GroupHeader from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/GroupHeader/GroupHeader.vue";
import ClauseBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/ClauseBuilder/ClauseBuilder.vue";

import {
    makeEmptyGroupPayload,
    setScope,
    toggleLogic,
    addChildGroupLikeParent,
    addEmptyLiteralClauseToGroup,
    removeClauseAtIndex as removeClauseAtIndexFromPayload,
    addRelationshipIfMissing,
    setGraphSlugAndResetIfChanged,
    removeChildGroupAtIndexAndReconcile,
    setClauseAtIndex,
    replaceChildGroupAtIndexAndReconcile,
    setRelationshipAndReconcileClauses,
} from "@/arches_search/AdvancedSearch/advanced-search-payload-builder.ts";

import {
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

defineOptions({ name: "GroupBuilder" });

type GraphSummary = {
    graphid: string;
    name: string;
    slug: string;
    id?: string;
    label?: string;
    [key: string]: unknown;
};

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

const emit = defineEmits<{
    (event: "update:modelValue", value: GroupPayload): void;
    (event: "remove"): void;
}>();

const { modelValue, isRoot, parentGroupAnchorGraph } = defineProps<{
    modelValue?: GroupPayload;
    isRoot?: boolean;
    parentGroupAnchorGraph?: GraphSummary;
}>();

const childGroupKeys = ref<string[]>([]);
const clauseKeys = ref<string[]>([]);

const currentGroup = computed<GroupPayload>(function getCurrentGroup() {
    return modelValue ?? makeEmptyGroupPayload();
});

const currentGroupAnchorGraph = computed<GraphSummary | null>(
    function getCurrentGroupAnchorGraph() {
        const allGraphs = graphs?.value ?? [];
        const groupSlug = currentGroup.value.graph_slug;

        if (!groupSlug) {
            return null;
        }

        const matchingGraph = allGraphs.find(
            function findMatchingGraph(candidateGraph) {
                return candidateGraph.slug === groupSlug;
            },
        );

        return matchingGraph ?? null;
    },
);

const effectiveAnchorGraph = computed<GraphSummary>(
    function getEffectiveAnchorGraph() {
        if (currentGroupAnchorGraph.value) {
            return currentGroupAnchorGraph.value;
        }

        if (parentGroupAnchorGraph) {
            return parentGroupAnchorGraph;
        }

        const fallbackSlug = currentGroup.value.graph_slug;

        return {
            graphid: fallbackSlug,
            name: fallbackSlug,
            slug: fallbackSlug,
        };
    },
);

const shouldHaveBracket = computed<boolean>(function getShouldHaveBracket() {
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

watchEffect(function () {
    childGroupKeys.value = buildStableKeys(
        childGroupKeys.value,
        currentGroup.value.groups.length,
    );

    clauseKeys.value = buildStableKeys(
        clauseKeys.value,
        currentGroup.value.clauses.length,
    );
});

function createStableKey(): string {
    return crypto.randomUUID();
}

function buildStableKeys(existingKeys: string[], nextCount: number): string[] {
    const nextKeys = existingKeys.slice(0, nextCount);

    while (nextKeys.length < nextCount) {
        nextKeys.push(createStableKey());
    }

    return nextKeys;
}

function emitUpdatedGroupPayload(nextGroupPayload: GroupPayload): void {
    emit("update:modelValue", nextGroupPayload);
}

function onSetGraphSlug(graphSlug: string): void {
    const updatedGroup = setGraphSlugAndResetIfChanged(
        currentGroup.value,
        graphSlug,
    );
    emitUpdatedGroupPayload(updatedGroup);
}

function onSetScope(scopeToken: GraphScopeToken): void {
    const updatedGroup = setScope(currentGroup.value, scopeToken);
    emitUpdatedGroupPayload(updatedGroup);
}

function onSetLogicFromBracket(_logicToken: LogicToken): void {
    const updatedGroup = toggleLogic(currentGroup.value);
    emitUpdatedGroupPayload(updatedGroup);
}

function onAddGroup(): void {
    const updatedGroup = addChildGroupLikeParent(currentGroup.value);
    emitUpdatedGroupPayload(updatedGroup);
}

function onRemoveChildGroup(childIndex: number): void {
    const updatedGroup = removeChildGroupAtIndexAndReconcile(
        currentGroup.value,
        childIndex,
    );
    emitUpdatedGroupPayload(updatedGroup);
}

function onAddClause(): void {
    const updatedGroup = addEmptyLiteralClauseToGroup(currentGroup.value);
    emitUpdatedGroupPayload(updatedGroup);
}

function onUpdateClauseAtIndex(
    updatedClause: unknown,
    clauseIndex: number,
): void {
    const safeUpdatedClause = updatedClause as GroupPayload["clauses"][number];
    const updatedGroup = setClauseAtIndex(
        currentGroup.value,
        clauseIndex,
        safeUpdatedClause,
    );
    emitUpdatedGroupPayload(updatedGroup);
}

function onRemoveClause(clauseIndex: number): void {
    const updatedGroup = removeClauseAtIndexFromPayload(
        currentGroup.value,
        clauseIndex,
    );
    emitUpdatedGroupPayload(updatedGroup);
}

function onAddRelationship(): void {
    const updatedGroup = addRelationshipIfMissing(currentGroup.value);
    emitUpdatedGroupPayload(updatedGroup);
}

function onRemoveRelationship(): void {
    const updatedGroup = setRelationshipAndReconcileClauses(
        currentGroup.value,
        null,
    );
    emitUpdatedGroupPayload(updatedGroup);
}

function onUpdateChildGroupModelValue(
    updatedChildGroupPayload: GroupPayload,
    childIndex: number,
): void {
    const updatedParentGroup = replaceChildGroupAtIndexAndReconcile(
        currentGroup.value,
        childIndex,
        updatedChildGroupPayload,
    );
    emitUpdatedGroupPayload(updatedParentGroup);
}

function onUpdateRelationship(
    nextRelationship: GroupPayload["relationship"],
): void {
    const updatedGroup = setRelationshipAndReconcileClauses(
        currentGroup.value,
        nextRelationship,
    );
    emitUpdatedGroupPayload(updatedGroup);
}

function onRequestRemoveGroup(): void {
    emit("remove");
}
</script>

<template>
    <Card class="group-card">
        <template #title>
            <GroupHeader
                :group-payload="currentGroup"
                :has-body-content="hasBodyContent"
                :has-nested-groups="currentGroup.groups.length > 0"
                :is-root="Boolean(isRoot)"
                @add-clause="onAddClause"
                @add-group="onAddGroup"
                @add-relationship="onAddRelationship"
                @change-graph="onSetGraphSlug"
                @change-scope="onSetScope"
                @remove-group="onRequestRemoveGroup"
                @remove-relationship="onRemoveRelationship"
                @update-relationship="onUpdateRelationship"
            />
        </template>

        <template #content>
            <div class="group-content">
                <div
                    :class="[
                        'group-grid',
                        shouldHaveBracket && 'group-grid-with-bracket',
                    ]"
                >
                    <GroupBracket
                        :show="shouldHaveBracket"
                        :logic="currentGroup.logic"
                        @update:logic="onSetLogicFromBracket"
                    />

                    <div class="group-body">
                        <div
                            v-if="currentGroup.clauses.length > 0"
                            :class="[
                                'clauses',
                                !shouldHaveBracket && 'clauses-without-bracket',
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
                                        :model-value="clause as any"
                                        :anchor-graph="effectiveAnchorGraph"
                                        :parent-group-anchor-graph="
                                            parentGroupAnchorGraph
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
                                !shouldHaveBracket &&
                                    'children-without-bracket',
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
                                @remove="onRemoveChildGroup(childIndex)"
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
