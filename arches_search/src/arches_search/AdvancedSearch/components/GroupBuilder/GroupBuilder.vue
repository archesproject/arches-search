<script setup lang="ts">
import { ref, computed, watchEffect, inject } from "vue";

import { useGettext } from "vue3-gettext";

import Card from "primevue/card";
import Button from "primevue/button";

import GroupBracket from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/GroupBracket.vue";
import GroupHeader from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/GroupHeader.vue";
import ClauseBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/ClauseBuilder/ClauseBuilder.vue";
import RelationshipEditor from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/RelationshipEditor.vue";

import {
    makeEmptyGroupPayload,
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

import { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";

import type {
    GraphModel,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

defineOptions({ name: "GroupBuilder" });

const { $gettext } = useGettext();

type RelationshipState = NonNullable<GroupPayload["relationship"]>;

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs");

const emit = defineEmits<{
    (event: "update:modelValue", value: GroupPayload): void;
    (event: "remove"): void;
}>();

const { modelValue, isRoot, parentGroupAnchorGraph, relationshipToParent } =
    defineProps<{
        modelValue?: GroupPayload;
        isRoot?: boolean;
        parentGroupAnchorGraph?: GraphModel;
        relationshipToParent?: RelationshipState | null;
    }>();

const childGroupKeys = ref<string[]>([]);
const clauseKeys = ref<string[]>([]);

const currentGroup = computed<GroupPayload>(function getCurrentGroup() {
    return modelValue ?? makeEmptyGroupPayload();
});

const currentGroupAnchorGraph = computed<GraphModel | null>(
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

const shouldHaveBracket = computed<boolean>(function () {
    return (
        currentGroup.value.groups.length + currentGroup.value.clauses.length >=
        2
    );
});

const hasGroupBodyContent = computed<boolean>(function () {
    return (
        currentGroup.value.clauses.length > 0 ||
        currentGroup.value.groups.length > 0
    );
});

const isGraphSelected = computed<boolean>(function () {
    const graphSlug = currentGroup.value.graph_slug ?? "";
    return graphSlug.trim().length > 0;
});

const hasNestedGroups = computed<boolean>(function () {
    return currentGroup.value.groups.length > 0;
});

const hasRelationship = computed<boolean>(function () {
    return currentGroup.value.relationship !== null;
});

const innerGraphSlug = computed<string>(function () {
    if (currentGroup.value.groups.length === 0) {
        return "";
    }

    return currentGroup.value.groups[0].graph_slug;
});

const relateButtonTitle = computed<string>(function () {
    if (!isGraphSelected.value) {
        return $gettext("Select what this group filters before relating.");
    }

    if (!hasNestedGroups.value) {
        return $gettext("Add a nested group below to enable relationships.");
    }

    if (hasRelationship.value) {
        return $gettext("This group is already related to its nested group.");
    }

    return $gettext("Relate this group to its nested group.");
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

function onSetLogicFromBracket(_logicToken: LogicToken): void {
    const updatedGroup = toggleLogic(currentGroup.value);
    emitUpdatedGroupPayload(updatedGroup);
}

function onAddGroup(): void {
    const existingChildGroups = currentGroup.value.groups;
    const updatedGroupWithNewChild = addChildGroupLikeParent(
        currentGroup.value,
    );

    if (existingChildGroups.length === 0) {
        emitUpdatedGroupPayload(updatedGroupWithNewChild);
        return;
    }

    const referenceChildGroup = existingChildGroups[0];
    const targetGraphSlug =
        referenceChildGroup.graph_slug || currentGroup.value.graph_slug;

    const nextChildGroups = updatedGroupWithNewChild.groups.slice();
    const newChildIndex = nextChildGroups.length - 1;

    if (newChildIndex >= 0) {
        const newChildGroup = nextChildGroups[newChildIndex];
        nextChildGroups[newChildIndex] = {
            ...newChildGroup,
            graph_slug: targetGraphSlug,
        };
    }

    const normalizedUpdatedGroup: GroupPayload = {
        ...updatedGroupWithNewChild,
        groups: nextChildGroups,
    };

    emitUpdatedGroupPayload(normalizedUpdatedGroup);
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

function deriveChildGraphSlugFromRelationship(
    anchorGraphSlug: string,
    nextRelationship: GroupPayload["relationship"],
): string {
    if (!nextRelationship) {
        return "";
    }

    const slugsInPath = nextRelationship.path
        .map((segment) => String(segment?.[0] ?? "").trim())
        .filter((slug) => slug.length > 0);

    if (slugsInPath.length === 0) {
        return "";
    }

    const otherSlugFromEnd = [...slugsInPath]
        .reverse()
        .find((slug) => slug !== anchorGraphSlug);

    if (otherSlugFromEnd) {
        return otherSlugFromEnd;
    }

    return slugsInPath[0] ?? "";
}

function onUpdateRelationship(
    nextRelationship: GroupPayload["relationship"],
): void {
    const updatedGroup = setRelationshipAndReconcileClauses(
        currentGroup.value,
        nextRelationship,
    );

    const anchorGraphSlug = updatedGroup.graph_slug ?? "";
    const previousChildAnchorGraphSlug =
        updatedGroup.groups[0]?.graph_slug ?? "";

    const nextChildAnchorGraphSlug = deriveChildGraphSlugFromRelationship(
        anchorGraphSlug,
        nextRelationship,
    );

    if (
        nextChildAnchorGraphSlug &&
        nextChildAnchorGraphSlug !== previousChildAnchorGraphSlug &&
        updatedGroup.groups.length > 0
    ) {
        const nextChildGroups = updatedGroup.groups.map((childGroup) => {
            return {
                ...childGroup,
                graph_slug: nextChildAnchorGraphSlug,
            };
        });

        const updatedGroupWithUpdatedChildren: GroupPayload = {
            ...updatedGroup,
            groups: nextChildGroups,
        };

        emitUpdatedGroupPayload(updatedGroupWithUpdatedChildren);
        return;
    }

    emitUpdatedGroupPayload(updatedGroup);
}

function onRequestRemoveGroup(): void {
    emit("remove");
}
</script>

<template>
    <Card
        class="group-card"
        :style="{
            borderRadius: isRoot && 0,
            borderBottom: isRoot && 'none',
        }"
    >
        <template #title>
            <GroupHeader
                :group-payload="currentGroup"
                :is-root="isRoot"
                :relationship-to-parent="relationshipToParent ?? null"
                @change-graph="onSetGraphSlug"
                @remove-group="onRequestRemoveGroup"
            />
            <RelationshipEditor
                v-if="hasRelationship"
                class="relationship-editor-inline"
                :anchor-graph-slug="currentGroup.graph_slug"
                :inner-graph-slug="innerGraphSlug"
                :is-root="isRoot"
                :relationship="currentGroup.relationship!"
                @update:relationship="onUpdateRelationship"
            />
        </template>

        <template #content>
            <div
                class="group-content"
                :class="hasGroupBodyContent && 'group-content-with-top-padding'"
            >
                <div
                    v-if="!hasGroupBodyContent && !currentGroupAnchorGraph"
                    class="group-helper-note"
                >
                    <div>
                        {{
                            $gettext(
                                "Add a filter to search the database. Groups let you bundle filters",
                            )
                        }}
                    </div>
                    <div>
                        {{
                            $gettext(
                                "Click the group type to change the type of grouping.",
                            )
                        }}
                    </div>
                </div>

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
                                        :model-value="clause"
                                        :anchor-graph="currentGroupAnchorGraph!"
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
                                    currentGroupAnchorGraph!
                                "
                                :relationship-to-parent="
                                    currentGroup.relationship ?? null
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

        <template #footer>
            <div
                class="group-footer-actions"
                :style="{
                    marginTop: hasGroupBodyContent ? '3rem' : '1rem',
                }"
            >
                <Button
                    severity="secondary"
                    icon="pi pi-table"
                    :label="$gettext('Add group')"
                    :disabled="!isGraphSelected"
                    @click.stop="onAddGroup"
                />
                <Button
                    severity="secondary"
                    icon="pi pi-filter"
                    :label="$gettext('Add filter')"
                    :disabled="!isGraphSelected"
                    @click.stop="onAddClause"
                />
                <Button
                    v-if="hasNestedGroups"
                    class="group-relate-button"
                    severity="secondary"
                    icon="pi pi-link"
                    :label="$gettext('Add relationship filter')"
                    :title="relateButtonTitle"
                    :disabled="hasRelationship"
                    @click.stop="onAddRelationship"
                />
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
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
    margin-inline-end: 0;
}

.group-card :deep(.p-card-body) {
    gap: 0;
    padding: 1rem;
}

.clause-card {
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
}

.group-content {
    display: flex;
    flex-direction: column;
}

.group-content-with-top-padding {
    padding-top: 1rem;
}

.group-grid {
    display: flex;
    align-items: stretch;
    width: 100%;
}

.group-grid-with-bracket {
    display: flex;
    align-items: stretch;
    padding-inline-start: 1.5rem;
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
    gap: 1rem;
}

.children {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.children .children > .group-card,
.children .clauses > .clause-card {
    margin-inline-end: 3rem;
}

.clauses-without-bracket,
.children-without-bracket {
    margin-inline-start: 2rem;
}

.relationship-editor-inline {
    align-self: stretch;
}

.group-footer-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    align-items: center;
}

.group-helper-note {
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
    margin-top: 1rem;
    margin-bottom: 1rem;
    margin-inline-start: 1.5rem;
}
</style>
