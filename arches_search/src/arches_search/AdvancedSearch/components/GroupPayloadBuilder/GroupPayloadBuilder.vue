<script setup lang="ts">
import {
    defineProps,
    defineEmits,
    ref,
    computed,
    watchEffect,
    defineOptions,
} from "vue";
import { useGettext } from "vue3-gettext";
import Button from "primevue/button";
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
    replaceChildGroupAtIndex,
    removeChildGroupAtIndex,
    addEmptyLiteralClauseToGroup,
    removeClauseAtIndex as removeClauseAtIndexFromPayload,
    addRelationshipIfMissing,
    clearRelationshipIfPresent,
    reconcileStableKeys,
} from "@/arches_search/AdvancedSearch/advanced-search-payload-builder.ts";

import GroupBracket from "@/arches_search/AdvancedSearch/components/GroupPayloadBuilder/components/GroupBracket.vue";
import GroupHeader from "@/arches_search/AdvancedSearch/components/GroupPayloadBuilder/components/GroupHeader.vue";

defineOptions({ name: "GroupPayloadBuilder" });

const { $gettext } = useGettext();

const emit = defineEmits<{
    (event: "update:modelValue", value: GroupPayload): void;
    (event: "remove"): void;
}>();

const props = defineProps<{
    modelValue?: GroupPayload;
    isRoot?: boolean;
}>();

const currentGroup = computed<GroupPayload>(function getCurrentGroup() {
    return props.modelValue ?? makeEmptyGroupPayload();
});

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
    commit(setGraphSlug(currentGroup.value, graphSlug));
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

function onReplaceChildGroup(
    childIndex: number,
    replacement: GroupPayload,
): void {
    const updatedParent = replaceChildGroupAtIndex(
        currentGroup.value,
        childIndex,
        replacement,
    );
    commit(updatedParent);
}

function onRemoveChildGroup(childIndex: number): void {
    const updatedParent = removeChildGroupAtIndex(
        currentGroup.value,
        childIndex,
    );
    commit(updatedParent);
}

function onAddClause(): void {
    commit(addEmptyLiteralClauseToGroup(currentGroup.value));
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
    onReplaceChildGroup(childIndex, updatedChildGroupPayload);
}

function onUpdateRelationship(
    nextRelationship: NonNullable<GroupPayload["relationship"]>,
): void {
    const updatedGroup: GroupPayload = {
        ...currentGroup.value,
        relationship: nextRelationship,
    };
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
                            class="clauses"
                        >
                            <div
                                v-for="(
                                    clause, clauseIndex
                                ) in currentGroup.clauses"
                                :key="clauseKeys[clauseIndex]"
                                class="clause-row"
                            >
                                <span class="clause-label">
                                    {{ $gettext("Clause") }}
                                    {{ clauseIndex + 1 }}
                                </span>
                                <Button
                                    severity="danger"
                                    icon="pi pi-trash"
                                    :label="$gettext('Remove clause')"
                                    @click.stop="onRemoveClause(clauseIndex)"
                                />
                            </div>
                        </div>

                        <div
                            v-if="currentGroup.groups.length > 0"
                            class="children"
                        >
                            <GroupPayloadBuilder
                                v-for="(
                                    childGroup, childIndex
                                ) in currentGroup.groups"
                                :key="childGroupKeys[childIndex]"
                                :model-value="childGroup"
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
    font-size: 1rem;
}

.group-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.group-grid {
    display: grid;
    grid-template-columns: 1fr;
    align-items: stretch;
}

.group-grid-with-bracket {
    grid-template-columns: 4rem 1fr;
}

.group-body {
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.group-grid-with-bracket .group-body {
    grid-column: 2;
}

.clauses {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.clause-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0.5rem;
    align-items: center;
}

.clause-label {
    white-space: nowrap;
}

.children {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}
</style>
