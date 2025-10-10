<script setup lang="ts">
import { computed, defineProps, defineEmits, useId } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import QueryClause from "@/arches_search/AdvancedSearch/components/QueryClause/QueryClause.vue";

import {
    addEmptyGroup,
    addEmptyClause,
    removeGroup,
    removeClause,
    updateGroupLogic,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

import type {
    GroupPayload,
    Clause,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

const { $gettext } = useGettext();

const { group, recursionDepth } = defineProps<{
    group: GroupPayload;
    recursionDepth?: number;
}>();

const emit = defineEmits<{
    (e: "request:removeGroup", targetGroup: GroupPayload): void;
}>();

const keyedClauses = computed(() =>
    group.clauses.map((currentClause) => ({
        clause: currentClause,
        key: useId(),
    })),
);

const keyedGroups = computed(() =>
    group.groups.map((currentGroup) => ({
        group: currentGroup,
        key: useId(),
    })),
);

function onToggleLogic() {
    updateGroupLogic(group, group.logic === "AND" ? "OR" : "AND");
}

function onAddSubgroup() {
    addEmptyGroup(group);
}

function onAddClause() {
    addEmptyClause(group);
}

function onRequestRemoveChild(targetGroup: GroupPayload) {
    removeGroup(group, targetGroup);
}

function onRequestRemoveClause(targetClause: Clause) {
    removeClause(group, targetClause);
}

function onRequestRemoveSelf() {
    emit("request:removeGroup", group);
}
</script>

<template>
    <div class="query-group">
        <div
            style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding-bottom: 1rem;
            "
        >
            <div>
                <Button
                    v-if="group.groups.length + group.clauses.length > 1"
                    :label="group.logic"
                    @click="onToggleLogic"
                />
            </div>
            <div>
                <Button
                    icon="pi pi-plus"
                    :label="$gettext('Add Group')"
                    @click="onAddSubgroup"
                />
                <Button
                    icon="pi pi-plus"
                    :label="$gettext('Add Clause')"
                    @click="onAddClause"
                />
                <Button
                    v-if="recursionDepth"
                    icon="pi pi-times"
                    severity="danger"
                    @click="onRequestRemoveSelf"
                />
            </div>
        </div>

        <div v-if="group.clauses.length">
            <QueryClause
                v-for="item in keyedClauses"
                :key="item.key"
                :clause="item.clause"
                @request:remove-clause="onRequestRemoveClause"
            />
        </div>

        <div v-if="group.groups.length">
            <QueryGroup
                v-for="item in keyedGroups"
                :key="item.key"
                :group="item.group"
                :recursion-depth="(recursionDepth || 0) + 1"
                @request:remove-group="onRequestRemoveChild"
            />
        </div>
    </div>
</template>

<style scoped>
.query-group {
    border: 0.125rem solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    background: var(--p-content-background);
    color: var(--p-text-color);
    padding: 1rem;
}
</style>
