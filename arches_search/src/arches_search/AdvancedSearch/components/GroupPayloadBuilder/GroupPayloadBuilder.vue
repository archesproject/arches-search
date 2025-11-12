<script setup lang="ts">
import {
    defineProps,
    defineEmits,
    inject,
    ref,
    computed,
    watchEffect,
    defineOptions,
} from "vue";
import { useGettext } from "vue3-gettext";
import Select from "primevue/select";
import Button from "primevue/button";
import Card from "primevue/card";
import Divider from "primevue/divider";

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

defineOptions({ name: "GroupPayloadBuilder" });

const { $gettext } = useGettext();

type GraphSummary =
    | { id?: string; slug: string; name?: string; label?: string }
    | Record<string, unknown>;

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

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

const scopeOptions = computed<{ label: string; value: GraphScopeToken }[]>(
    function getScopeOptions() {
        return [
            { label: $gettext("Resource"), value: GraphScopeToken.RESOURCE },
            { label: $gettext("Tile"), value: GraphScopeToken.TILE },
        ];
    },
);

const graphOptions = computed<{ label: string; value: string }[]>(
    function getGraphOptions() {
        const availableGraphs = graphs?.value ?? [];
        return availableGraphs
            .map(function toOption(entry: GraphSummary) {
                const slug = (entry as { slug?: string }).slug ?? "";
                const displayName =
                    (entry as { name?: string }).name ??
                    (entry as { label?: string }).label ??
                    slug;
                return { label: String(displayName), value: String(slug) };
            })
            .filter(function nonEmpty(option) {
                return option.value.length > 0;
            });
    },
);

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
    if (
        typeof crypto !== "undefined" &&
        typeof crypto.randomUUID === "function"
    ) {
        return crypto.randomUUID();
    }
    const randomSuffix = Math.floor(Math.random() * 1e9).toString(36);
    return `k_${Date.now().toString(36)}_${randomSuffix}`;
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

function onSetLogicFromBracket(_nextLogicToken: LogicToken): void {
    commit(toggleLogic(currentGroup.value));
}

function onAddGroup(): void {
    const newChildGroup: GroupPayload = {
        ...makeEmptyGroupPayload(),
        graph_slug: currentGroup.value.graph_slug,
        scope: currentGroup.value.scope,
        logic: LogicToken.AND,
    };

    const updatedParent: GroupPayload = {
        ...currentGroup.value,
        groups: [...currentGroup.value.groups, newChildGroup],
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
</script>

<template>
    <Card class="group-card">
        <template #title>
            <div class="group-header">
                <div class="group-selectors">
                    <Select
                        :model-value="currentGroup.graph_slug"
                        :options="graphOptions"
                        option-label="label"
                        option-value="value"
                        :placeholder="$gettext('Select graph')"
                        class="group-field"
                        @update:model-value="onSetGraphSlug"
                    />
                    <Select
                        :model-value="currentGroup.scope"
                        :options="scopeOptions"
                        option-label="label"
                        option-value="value"
                        class="group-field"
                        @update:model-value="onSetScope"
                    />
                </div>

                <div class="group-actions">
                    <Button
                        severity="secondary"
                        icon="pi pi-plus"
                        :label="$gettext('Add group')"
                        @click.stop="onAddGroup"
                    />
                    <Button
                        severity="secondary"
                        icon="pi pi-plus"
                        :label="$gettext('Add clause')"
                        @click.stop="onAddClause"
                    />
                    <Button
                        v-if="currentGroup.relationship === null"
                        severity="secondary"
                        icon="pi pi-link"
                        :label="$gettext('Add relationship')"
                        @click.stop="onAddRelationship"
                    />
                    <Button
                        v-else
                        severity="danger"
                        icon="pi pi-unlink"
                        :label="$gettext('Remove relationship')"
                        @click.stop="onRemoveRelationship"
                    />
                    <Button
                        v-if="!props.isRoot"
                        severity="danger"
                        icon="pi pi-times"
                        :label="$gettext('Remove group')"
                        @click.stop="$emit('remove')"
                    />
                </div>
            </div>
        </template>

        <template #content>
            <div
                :class="[
                    'group-grid',
                    hasBracket ? 'group-grid-with-bracket' : '',
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
                                unusedClause, clauseIndex
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
                        <Divider />
                    </div>

                    <div
                        v-if="currentGroup.groups.length > 0"
                        class="children"
                    >
                        <GroupPayloadBuilder
                            v-for="(
                                unusedChildGroup, childIndex
                            ) in currentGroup.groups"
                            :key="childGroupKeys[childIndex]"
                            :model-value="currentGroup.groups[childIndex]"
                            @update:model-value="
                                (updatedChildGroupPayload) =>
                                    onReplaceChildGroup(
                                        childIndex,
                                        updatedChildGroupPayload,
                                    )
                            "
                            @remove="() => onRemoveChildGroup(childIndex)"
                        />
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
    border: 0.0625rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
}

.group-header {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0.75rem;
    align-items: center;
}

.group-selectors {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
}

.group-field {
    min-width: 12rem;
}

.group-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
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
