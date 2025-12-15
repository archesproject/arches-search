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

const isRelationshipContainer = computed<boolean>(
    function getIsRelationshipContainer() {
        return currentGroup.value.relationship !== null;
    },
);

const relationshipInnerGroup = computed<GroupPayload | null>(
    function getRelationshipInnerGroup() {
        if (!isRelationshipContainer.value) {
            return null;
        }

        const firstChild = currentGroup.value.groups[0];
        if (!firstChild) {
            return null;
        }

        return firstChild;
    },
);

const visibleGroup = computed<GroupPayload>(function getVisibleGroup() {
    return relationshipInnerGroup.value ?? currentGroup.value;
});

const groupHeaderPayload = computed<GroupPayload>(
    function getGroupHeaderPayload() {
        if (isRoot) {
            return currentGroup.value;
        }

        return visibleGroup.value;
    },
);

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

const visibleGroupAnchorGraph = computed<GraphModel | null>(
    function getVisibleGroupAnchorGraph() {
        const allGraphs = graphs?.value ?? [];
        const groupSlug = visibleGroup.value.graph_slug;

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

const shouldHaveBracket = computed<boolean>(function getShouldHaveBracket() {
    return (
        visibleGroup.value.groups.length + visibleGroup.value.clauses.length >=
        2
    );
});

const hasGroupBodyContent = computed<boolean>(
    function getHasGroupBodyContent() {
        return (
            visibleGroup.value.clauses.length > 0 ||
            visibleGroup.value.groups.length > 0
        );
    },
);

const isGraphSelected = computed<boolean>(function getIsGraphSelected() {
    const graphSlug = currentGroup.value.graph_slug ?? "";
    return graphSlug.trim().length > 0;
});

const hasNestedGroups = computed<boolean>(function getHasNestedGroups() {
    return currentGroup.value.groups.length > 0;
});

const hasRelationship = computed<boolean>(function getHasRelationship() {
    return currentGroup.value.relationship !== null;
});

const shouldRenderCardTitle = computed<boolean>(
    function getShouldRenderCardTitle() {
        return (
            Boolean(isRoot) ||
            relationshipToParent != null ||
            hasRelationship.value
        );
    },
);

const shouldRenderGroupHeader = computed<boolean>(
    function getShouldRenderGroupHeader() {
        return Boolean(isRoot) || relationshipToParent != null;
    },
);

const hasRelationshipInImmediateChildren = computed<boolean>(
    function getHasRelationshipInImmediateChildren() {
        return currentGroup.value.groups.some(
            function doesChildHaveRelationship(childGroup) {
                return childGroup.relationship !== null;
            },
        );
    },
);

const innerGraphSlug = computed<string>(function getInnerGraphSlug() {
    if (currentGroup.value.groups.length === 0) {
        return "";
    }

    return currentGroup.value.groups[0].graph_slug;
});

const relateButtonTitle = computed<string>(function getRelateButtonTitle() {
    if (!isGraphSelected.value) {
        return $gettext("Select what this group filters before relating.");
    }

    if (!hasNestedGroups.value) {
        return $gettext("Add a nested group below to enable relationships.");
    }

    if (hasRelationshipInImmediateChildren.value) {
        return $gettext("A relationship filter already exists one level down.");
    }

    return $gettext("Add a relationship filter as a nested group.");
});

const footerMarginTop = computed<string>(function () {
    if (hasGroupBodyContent.value || hasRelationship.value) {
        return "0rem";
    }

    return "0";
});

watchEffect(function syncStableKeys() {
    childGroupKeys.value = buildStableKeys(
        childGroupKeys.value,
        visibleGroup.value.groups.length,
    );
    clauseKeys.value = buildStableKeys(
        clauseKeys.value,
        visibleGroup.value.clauses.length,
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

function setVisibleGroupOnCurrentGroup(
    nextVisibleGroup: GroupPayload,
): GroupPayload {
    if (!isRelationshipContainer.value) {
        return nextVisibleGroup;
    }

    const existingGroups = currentGroup.value.groups.slice();
    const restGroups = existingGroups.slice(1);

    return {
        ...currentGroup.value,
        groups: [nextVisibleGroup, ...restGroups],
    };
}

function onSetGraphSlug(graphSlug: string): void {
    const updatedGroup = setGraphSlugAndResetIfChanged(
        currentGroup.value,
        graphSlug,
    );
    emitUpdatedGroupPayload(updatedGroup);
}

function onSetLogicFromBracket(_logicToken: LogicToken): void {
    const updatedVisibleGroup = toggleLogic(visibleGroup.value);
    emitUpdatedGroupPayload(setVisibleGroupOnCurrentGroup(updatedVisibleGroup));
}

function onAddGroup(): void {
    const baseGroup = visibleGroup.value;

    const existingChildGroups = baseGroup.groups;
    const updatedGroupWithNewChild = addChildGroupLikeParent(baseGroup);

    if (existingChildGroups.length === 0) {
        emitUpdatedGroupPayload(
            setVisibleGroupOnCurrentGroup(updatedGroupWithNewChild),
        );
        return;
    }

    const referenceChildGroup = existingChildGroups[0];
    const targetGraphSlug =
        referenceChildGroup.graph_slug || baseGroup.graph_slug;

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

    emitUpdatedGroupPayload(
        setVisibleGroupOnCurrentGroup(normalizedUpdatedGroup),
    );
}

function onRemoveChildGroup(childIndex: number): void {
    const updatedVisibleGroup = removeChildGroupAtIndexAndReconcile(
        visibleGroup.value,
        childIndex,
    );
    emitUpdatedGroupPayload(setVisibleGroupOnCurrentGroup(updatedVisibleGroup));
}

function onAddClause(): void {
    const updatedVisibleGroup = addEmptyLiteralClauseToGroup(
        visibleGroup.value,
    );
    emitUpdatedGroupPayload(setVisibleGroupOnCurrentGroup(updatedVisibleGroup));
}

function onUpdateClauseAtIndex(
    updatedClause: unknown,
    clauseIndex: number,
): void {
    const safeUpdatedClause = updatedClause as GroupPayload["clauses"][number];
    const updatedVisibleGroup = setClauseAtIndex(
        visibleGroup.value,
        clauseIndex,
        safeUpdatedClause,
    );
    emitUpdatedGroupPayload(setVisibleGroupOnCurrentGroup(updatedVisibleGroup));
}

function onRemoveClause(clauseIndex: number): void {
    const updatedVisibleGroup = removeClauseAtIndexFromPayload(
        visibleGroup.value,
        clauseIndex,
    );
    emitUpdatedGroupPayload(setVisibleGroupOnCurrentGroup(updatedVisibleGroup));
}

function ensureRelationshipContainerHasNestedChild(
    relationshipContainerGroup: GroupPayload,
): GroupPayload {
    if (relationshipContainerGroup.groups.length > 0) {
        return relationshipContainerGroup;
    }

    const relationshipContainerWithChild = addChildGroupLikeParent(
        relationshipContainerGroup,
    );

    if (relationshipContainerWithChild.groups.length === 0) {
        return relationshipContainerWithChild;
    }

    const nestedChildGroups = relationshipContainerWithChild.groups.slice();
    nestedChildGroups[0] = {
        ...nestedChildGroups[0],
        graph_slug: "",
    };

    return {
        ...relationshipContainerWithChild,
        groups: nestedChildGroups,
    };
}

function addRelationshipFilterChildGroup(
    parentGroupPayload: GroupPayload,
): GroupPayload {
    const updatedParentGroupWithNewChild =
        addChildGroupLikeParent(parentGroupPayload);

    const newChildIndex = updatedParentGroupWithNewChild.groups.length - 1;
    if (newChildIndex < 0) {
        return updatedParentGroupWithNewChild;
    }

    const newlyAddedChildGroup =
        updatedParentGroupWithNewChild.groups[newChildIndex];

    const relationshipContainerSeededToParentGraph: GroupPayload = {
        ...newlyAddedChildGroup,
        graph_slug: parentGroupPayload.graph_slug,
    };

    const relationshipContainerWithRelationship = addRelationshipIfMissing(
        relationshipContainerSeededToParentGraph,
    );

    const relationshipContainerReady =
        ensureRelationshipContainerHasNestedChild(
            relationshipContainerWithRelationship,
        );

    const nextChildGroups = updatedParentGroupWithNewChild.groups.slice();
    nextChildGroups[newChildIndex] = relationshipContainerReady;

    return {
        ...updatedParentGroupWithNewChild,
        groups: nextChildGroups,
    };
}

function onAddRelationship(): void {
    const updatedVisibleGroup = addRelationshipFilterChildGroup(
        visibleGroup.value,
    );
    emitUpdatedGroupPayload(setVisibleGroupOnCurrentGroup(updatedVisibleGroup));
}

function onUpdateChildGroupModelValue(
    updatedChildGroupPayload: GroupPayload,
    childIndex: number,
): void {
    const updatedVisibleGroup = replaceChildGroupAtIndexAndReconcile(
        visibleGroup.value,
        childIndex,
        updatedChildGroupPayload,
    );
    emitUpdatedGroupPayload(setVisibleGroupOnCurrentGroup(updatedVisibleGroup));
}

function onUpdateRelationship(
    nextRelationship: GroupPayload["relationship"],
): void {
    if (!nextRelationship) {
        emit("remove");
        return;
    }

    const updatedGroup = ensureRelationshipContainerHasNestedChild(
        setRelationshipAndReconcileClauses(
            currentGroup.value,
            nextRelationship,
        ),
    );

    emitUpdatedGroupPayload(updatedGroup);
}

function onUpdateInnerGraphSlug(nextInnerGraphSlugRaw: string): void {
    if (currentGroup.value.groups.length === 0) {
        return;
    }

    const nextInnerGraphSlug = String(nextInnerGraphSlugRaw ?? "").trim();

    const nextChildGroups = currentGroup.value.groups.slice();
    nextChildGroups[0] = {
        ...nextChildGroups[0],
        graph_slug: nextInnerGraphSlug,
    };

    const existingRelationship = currentGroup.value.relationship;

    const nextRelationship: GroupPayload["relationship"] = existingRelationship
        ? { ...existingRelationship, path: [] }
        : null;

    const updatedGroup = setRelationshipAndReconcileClauses(
        {
            ...currentGroup.value,
            groups: nextChildGroups,
        },
        nextRelationship,
    );

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
        <template
            v-if="shouldRenderCardTitle"
            #title
        >
            <GroupHeader
                v-if="shouldRenderGroupHeader"
                :group-payload="groupHeaderPayload"
                :is-root="isRoot"
                :relationship-to-parent="relationshipToParent ?? null"
                @change-graph="onSetGraphSlug"
                @remove-group="onRequestRemoveGroup"
            />

            <RelationshipEditor
                v-if="hasRelationship"
                class="relationship-editor-inline"
                :style="{
                    marginBottom: !hasGroupBodyContent ? '1.5rem' : 0,
                }"
                :anchor-graph-slug="currentGroup.graph_slug"
                :inner-graph-slug="innerGraphSlug"
                :relationship="currentGroup.relationship!"
                @update:relationship="onUpdateRelationship"
                @update:inner-graph-slug="onUpdateInnerGraphSlug"
            />
        </template>

        <template #content>
            <div
                class="group-content"
                :class="
                    hasGroupBodyContent &&
                    hasRelationship &&
                    'group-content-with-top-padding'
                "
            >
                <div
                    v-if="
                        isRoot &&
                        !hasGroupBodyContent &&
                        !currentGroupAnchorGraph
                    "
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
                    v-if="hasGroupBodyContent"
                    :class="[
                        'group-grid',
                        shouldHaveBracket && 'group-grid-with-bracket',
                    ]"
                >
                    <GroupBracket
                        :show="shouldHaveBracket"
                        :logic="visibleGroup.logic"
                        @update:logic="onSetLogicFromBracket"
                    />

                    <div class="group-body">
                        <div
                            v-if="visibleGroup.clauses.length > 0"
                            :class="[
                                'clauses',
                                !isRoot &&
                                    !shouldHaveBracket &&
                                    'clauses-without-bracket',
                            ]"
                            :style="{
                                marginInlineEnd: isRoot ? 0 : '2.5rem',
                            }"
                        >
                            <Card
                                v-for="(
                                    clause, clauseIndex
                                ) in visibleGroup.clauses"
                                :key="clauseKeys[clauseIndex]"
                                class="clause-card"
                                :style="{}"
                            >
                                <template #content>
                                    <ClauseBuilder
                                        :model-value="clause"
                                        :anchor-graph="visibleGroupAnchorGraph!"
                                        :parent-group-anchor-graph="
                                            isRelationshipContainer
                                                ? currentGroupAnchorGraph!
                                                : parentGroupAnchorGraph
                                        "
                                        :relationship="
                                            currentGroup.relationship
                                        "
                                        :inner-group-graph-slug="
                                            isRelationshipContainer
                                                ? visibleGroup.graph_slug
                                                : currentGroup.groups[0]
                                                      ?.graph_slug
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
                            v-if="visibleGroup.groups.length > 0"
                            :class="[
                                'children',
                                !isRoot &&
                                    !shouldHaveBracket &&
                                    'children-without-bracket',
                            ]"
                            :style="{
                                marginInlineEnd: isRoot ? 0 : '2.5rem',
                            }"
                        >
                            <GroupBuilder
                                v-for="(
                                    childGroup, childIndex
                                ) in visibleGroup.groups"
                                :key="childGroupKeys[childIndex]"
                                :model-value="childGroup"
                                :parent-group-anchor-graph="
                                    visibleGroupAnchorGraph!
                                "
                                :relationship-to-parent="
                                    childGroup.relationship ?? null
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
                :style="{ marginTop: footerMarginTop }"
            >
                <Button
                    severity="secondary"
                    icon="pi pi-table"
                    :label="$gettext('Add group')"
                    :disabled="!visibleGroupAnchorGraph"
                    @click.stop="onAddGroup"
                />
                <Button
                    severity="secondary"
                    icon="pi pi-filter"
                    :label="$gettext('Add filter')"
                    :disabled="!visibleGroupAnchorGraph"
                    @click.stop="onAddClause"
                />
                <Button
                    class="group-relate-button"
                    severity="secondary"
                    icon="pi pi-link"
                    :label="$gettext('Add relationship filter')"
                    :title="relateButtonTitle"
                    :disabled="!visibleGroupAnchorGraph"
                    @click.stop="onAddRelationship"
                />

                <div
                    v-if="!isRoot"
                    class="group-footer-remove"
                >
                    <Button
                        severity="danger"
                        icon="pi pi-trash"
                        variant="outlined"
                        :label="$gettext('Remove group')"
                        :aria-label="$gettext('Remove group')"
                        @click.stop="onRequestRemoveGroup"
                    />
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
    /* width: fit-content; */
}

.group-content-with-top-padding {
    /* padding-top: 1rem; */
}

.group-grid {
    display: flex;
    align-items: stretch;
    width: 100%;
    margin-top: 1rem;
    margin-bottom: 1.75rem;
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
    /* margin-bottom: 1rem; */
}

.clauses {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    /* margin-inline-end: 2.5rem; */
}

.children {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    /* margin-inline-end: 2.5rem; */
}

.children .children > .group-card,
.children .clauses > .clause-card {
    margin-inline-end: 3rem;
}

.clauses-without-bracket,
.children-without-bracket {
    margin-inline-start: 5.5rem;
}

.relationship-editor-inline {
    align-self: stretch;
}

.group-footer-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    align-items: center;
    margin-top: 0rem;
}

.group-footer-remove {
    margin-inline-start: auto;
    display: flex;
    flex: 0 0 auto;
}

.group-helper-note {
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
    margin-bottom: 2rem;
    margin-inline-start: 1.5rem;
}
</style>
