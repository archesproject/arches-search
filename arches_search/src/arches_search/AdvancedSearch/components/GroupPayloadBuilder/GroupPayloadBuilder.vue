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
    type GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

import {
    makeEmptyGroupPayload,
    setGraphSlug,
    setScope,
    toggleLogic,
    addChildGroupLikeParent,
    replaceChildGroupAtIndex,
    removeChildGroupAtIndex,
    addEmptyLiteralClauseToGroup,
    removeClauseAtIndex as removeClauseAtIndexFromPayload,
    addRelationshipIfMissing,
    clearRelationshipIfPresent,
    computeIsAnd,
    reconcileStableKeys,
} from "@/arches_search/AdvancedSearch/advanced-search-payload-builder.ts";

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

const isAnd = computed<boolean>(function getIsAnd() {
    return computeIsAnd(currentGroup.value);
});
const logicLabel = computed<string>(function getLogicLabel() {
    return isAnd.value ? $gettext("AND") : $gettext("OR");
});
const hasBracket = computed<boolean>(function getHasBracket() {
    return (
        currentGroup.value.groups.length + currentGroup.value.clauses.length >=
        2
    );
});

const scopeOptions = computed(() => [
    { label: $gettext("Resource"), value: GraphScopeToken.RESOURCE },
    { label: $gettext("Tile"), value: GraphScopeToken.TILE },
]);

const graphOptions = computed(() => {
    const list = graphs?.value ?? [];
    return list
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
});

watchEffect(function () {
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
function onToggleLogic(): void {
    commit(toggleLogic(currentGroup.value));
}
function onAddGroup(): void {
    commit(addChildGroupLikeParent(currentGroup.value));
}
function onReplaceChildGroup(
    childIndex: number,
    replacement: GroupPayload,
): void {
    commit(
        replaceChildGroupAtIndex(currentGroup.value, childIndex, replacement),
    );
}
function onRemoveChildGroup(childIndex: number): void {
    commit(removeChildGroupAtIndex(currentGroup.value, childIndex));
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
    <div class="group">
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
                            @click="onAddGroup"
                        />
                        <Button
                            severity="secondary"
                            icon="pi pi-plus"
                            :label="$gettext('Add clause')"
                            @click="onAddClause"
                        />
                        <Button
                            v-if="currentGroup.relationship === null"
                            severity="secondary"
                            icon="pi pi-link"
                            :label="$gettext('Add relationship')"
                            @click="onAddRelationship"
                        />
                        <Button
                            v-else
                            severity="danger"
                            icon="pi pi-unlink"
                            :label="$gettext('Remove relationship')"
                            @click="onRemoveRelationship"
                        />
                        <Button
                            v-if="!isRoot"
                            severity="danger"
                            icon="pi pi-times"
                            :label="$gettext('Remove group')"
                            @click="$emit('remove')"
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
                    <div
                        v-if="hasBracket"
                        :class="[
                            'bracket',
                            isAnd ? 'bracket-and' : 'bracket-or',
                        ]"
                    >
                        <div class="bracket-arm bracket-arm-top"></div>
                        <div class="bracket-spine bracket-spine-top"></div>
                        <div class="bracket-lane">
                            <Button
                                :label="logicLabel"
                                class="bracket-logic"
                                size="small"
                                @click="onToggleLogic"
                            />
                        </div>
                        <div class="bracket-spine bracket-spine-bottom"></div>
                        <div class="bracket-arm bracket-arm-bottom"></div>
                    </div>

                    <div class="group-body">
                        <div
                            v-if="currentGroup.clauses.length > 0"
                            class="clauses"
                        >
                            <div
                                v-for="(_, clauseIndex) in currentGroup.clauses"
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
                                    @click="onRemoveClause(clauseIndex)"
                                />
                            </div>
                            <Divider />
                        </div>

                        <div
                            v-if="currentGroup.groups.length > 0"
                            class="children"
                        >
                            <GroupPayloadBuilder
                                v-for="(_, childIndex) in currentGroup.groups"
                                :key="childGroupKeys[childIndex]"
                                :model-value="currentGroup.groups[childIndex]"
                                @update:model-value="
                                    function onChildUpdate(
                                        updatedGroupPayload,
                                    ) {
                                        onReplaceChildGroup(
                                            childIndex,
                                            updatedGroupPayload,
                                        );
                                    }
                                "
                                @remove="
                                    function onChildRemove() {
                                        onRemoveChildGroup(childIndex);
                                    }
                                "
                            />
                        </div>
                    </div>
                </div>
            </template>
        </Card>
    </div>
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

.bracket {
    display: grid;
    grid-template-columns: 0.3rem 1.75rem;
    grid-template-rows: 1fr auto 1fr;
    align-items: center;
    justify-items: start;
    padding-inline-start: 0.5rem;
    row-gap: 0.75rem;
}

.bracket-and {
    --logic-color: var(--p-blue-600);
    --logic-hover-color: var(--p-blue-700);
}

.bracket-or {
    --logic-color: var(--p-orange-600);
    --logic-hover-color: var(--p-orange-700);
}

.bracket-spine {
    width: 0.3rem;
    background: var(--logic-color);
    grid-column: 1;
    margin-inline-start: 0.75rem;
}

.bracket-spine-top {
    grid-row: 1;
    align-self: stretch;
}

.bracket-spine-bottom {
    grid-row: 3;
    align-self: stretch;
}

.bracket-lane {
    grid-column: 1;
    grid-row: 2;
    display: grid;
    place-items: center;
    width: 0.3rem;
}

.bracket-arm {
    background: var(--logic-color);
    height: 0.3rem;
    grid-column: 2;
    width: 100%;
    margin-inline-start: 0.75rem;
}

.bracket-arm-top {
    grid-row: 1;
    align-self: start;
}

.bracket-arm-bottom {
    grid-row: 3;
    align-self: end;
}

.bracket-logic.p-button {
    background: var(--logic-color);
    border-color: var(--logic-color);
    color: var(--p-surface-0);
    padding-block: 0.25rem;
    padding-inline: 0.75rem;
    box-shadow: none;
}

.bracket-logic.p-button:enabled:hover {
    background: var(--logic-hover-color);
    border-color: var(--logic-hover-color);
    color: var(--p-surface-0);
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
