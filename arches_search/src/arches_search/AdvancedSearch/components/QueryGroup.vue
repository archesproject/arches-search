<script setup lang="ts">
import {
    computed,
    defineEmits,
    defineProps,
    inject,
    ref,
    useId,
    watch,
} from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Dropdown from "primevue/dropdown";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";

import QueryClause from "@/arches_search/AdvancedSearch/components/QueryClause/QueryClause.vue";

import {
    addEmptyGroup,
    addEmptyClause,
    removeGroup,
    removeClause,
    updateGroupLogic,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

import type { Ref } from "vue";
import type {
    GroupPayload,
    Clause,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

const AND = "AND";
const OR = "OR";

const { $gettext } = useGettext();

const { group, recursionDepth } = defineProps<{
    group: GroupPayload;
    recursionDepth?: number;
}>();

const emit = defineEmits<{
    (e: "request:removeGroup", targetGroup: GroupPayload): void;
}>();

const isLoading = ref(false);
const configurationError = ref<Error>();

const graphs = inject<Ref<Record<string, unknown>[]>>("graphs")!;
const selectedGraph = ref<Record<string, unknown> | undefined>();

watch(
    () => group,
    (updatedGroup) => {
        const graphSlug = updatedGroup?.graph_slug;

        if (graphSlug) {
            selectedGraph.value = graphs.value.find(
                (graph) => graph.slug === graphSlug,
            );
        } else {
            selectedGraph.value = undefined;
        }
    },
    { immediate: true },
);

const isRootGroup = computed(() => {
    if (!recursionDepth) {
        return true;
    }

    return recursionDepth === 0;
});

const keyedClauses = computed(() => {
    return group.clauses.map((currentClause) => {
        return { clause: currentClause, key: useId() };
    });
});

const keyedGroups = computed(() => {
    return group.groups.map((currentGroup) => {
        return { group: currentGroup, key: useId() };
    });
});

function onToggleLogic() {
    const newLogic = group.logic === AND ? OR : AND;
    updateGroupLogic(group, newLogic);
}

function onAddSubgroup() {
    addEmptyGroup(group);
}

function onAddClause() {
    addEmptyClause(group);
}

function onRemoveChildGroup(target: GroupPayload) {
    removeGroup(group, target);
}

function onRemoveClause(target: Clause) {
    removeClause(group, target);
}

function onRemoveSelf() {
    emit("request:removeGroup", group);
}
</script>

<template>
    <Skeleton
        v-if="isLoading"
        style="height: 100%"
    />
    <Message
        v-else-if="configurationError"
        severity="error"
    >
        {{ configurationError.message }}
    </Message>
    <div
        v-else
        class="query-group"
    >
        <div class="query-group-controls">
            <div>
                <Button
                    v-if="group.groups.length + group.clauses.length > 1"
                    :label="group.logic"
                    @click="onToggleLogic"
                />
                <Dropdown
                    v-model="selectedGraph"
                    :options="graphs"
                    option-label="name"
                    :placeholder="$gettext('Select graph…')"
                />
            </div>

            <div style="display: flex; gap: 0.5rem">
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
                    v-if="!isRootGroup"
                    icon="pi pi-times"
                    severity="danger"
                    @click="onRemoveSelf"
                />
            </div>
        </div>

        <div v-if="group.clauses.length">
            <QueryClause
                v-for="item in keyedClauses"
                :key="item.key"
                :clause="item.clause"
                @request:remove-clause="onRemoveClause"
            />
        </div>

        <div v-if="group.groups.length">
            <QueryGroup
                v-for="item in keyedGroups"
                :key="item.key"
                :group="item.group"
                :recursion-depth="(recursionDepth || 0) + 1"
                @request:remove-group="onRemoveChildGroup"
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
    display: flex;
    flex-direction: column;
    padding: 1rem;
    width: 100%;
}

.query-group-controls {
    display: flex;
    justify-content: space-between;
    width: 100%;
}
</style>
