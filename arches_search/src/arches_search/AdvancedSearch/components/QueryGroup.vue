<script setup lang="ts">
import { defineOptions, defineProps, defineEmits } from "vue";
import Button from "primevue/button";
import QueryClause from "@/arches_search/AdvancedSearch/components/QueryClause.vue";
import type {
    GroupPayload,
    Clause,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";
import {
    toggleGroupLogic,
    addEmptyGroup,
    addEmptyClause,
    removeGroup as removeChildGroup,
    removeClause as removeChildClause,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

defineOptions({ name: "QueryGroup" });

type GraphNodeOption = { [key: string]: unknown };
type QueryRenderConfig = { nodeLabelKey?: string; nodeValueKey?: string };

const props = defineProps<{
    group: GroupPayload;
    nodes: GraphNodeOption[];
    config?: QueryRenderConfig;
    isRoot?: boolean;
}>();

const emit = defineEmits<{
    (e: "request-remove", targetGroup: GroupPayload): void;
    (e: "reset-all"): void;
}>();

function onToggleLogic() {
    toggleGroupLogic(props.group);
}
function onAddSubgroup() {
    addEmptyGroup(props.group);
}
function onAddClause() {
    addEmptyClause(props.group);
}
function onRemoveSelf() {
    if (props.isRoot) {
        emit("reset-all");
    } else {
        emit("request-remove", props.group);
    }
}
function onRequestRemoveChild(targetGroup: GroupPayload) {
    removeChildGroup(props.group, targetGroup);
}
function onRequestRemoveClause(targetClause: Clause) {
    removeChildClause(props.group, targetClause);
}
</script>

<template>
    <div class="query-group">
        <div class="query-group__header">
            <Button
                class="query-group__toggle"
                :label="group.logic"
                :aria-pressed="group.logic === 'OR'"
                @click="onToggleLogic"
            />
            <div class="query-group__actions">
                <Button
                    class="query-group__add-group"
                    label="Add Group"
                    icon="pi pi-plus"
                    @click="onAddSubgroup"
                />
                <Button
                    class="query-group__add-clause"
                    label="Add Clause"
                    icon="pi pi-plus"
                    @click="onAddClause"
                />
                <Button
                    class="query-group__remove-group"
                    :label="isRoot ? 'Reset' : 'Remove Group'"
                    icon="pi pi-trash"
                    severity="danger"
                    @click="onRemoveSelf"
                />
            </div>
        </div>

        <div
            v-if="group.clauses.length"
            class="query-group__clauses"
        >
            <QueryClause
                v-for="(existingClause, existingClauseIndex) in group.clauses"
                :key="existingClauseIndex"
                :clause="existingClause"
                :nodes="nodes"
                :config="config"
                @request-remove-clause="onRequestRemoveClause"
            />
        </div>

        <div
            v-if="group.groups.length"
            class="query-group__children"
        >
            <QueryGroup
                v-for="(childGroup, childGroupIndex) in group.groups"
                :key="childGroupIndex"
                :group="childGroup"
                :nodes="nodes"
                :config="config"
                @request-remove="onRequestRemoveChild"
            />
        </div>
    </div>
</template>

<style scoped>
.query-group {
    border: 1px solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    padding: 12px;
    background: var(--p-content-background);
    color: var(--p-text-color);
}
.query-group__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
}
.query-group__actions {
    display: flex;
    gap: 8px;
}
.query-group__toggle {
    min-width: 80px;
}
.query-group__clauses {
    display: grid;
    gap: 10px;
    margin-top: 8px;
}
.query-group__children {
    display: grid;
    gap: 12px;
    margin-top: 8px;
}
</style>
