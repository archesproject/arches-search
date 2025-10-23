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
import Select from "primevue/select";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";

import QueryClause from "@/arches_search/AdvancedSearch/components/QueryClause/QueryClause.vue";

import {
    addEmptyGroup,
    addEmptyClause,
    removeGroup,
    removeClause,
    updateGroupLogic,
    updateGroupGraphSlug,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

import type { Ref } from "vue";
import type {
    GroupPayload,
    Clause,
} from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

const AND = "AND";
const OR = "OR";

const { $gettext } = useGettext();

const { groupPayload, recursionDepth } = defineProps<{
    groupPayload: GroupPayload;
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
    () => groupPayload,
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

watch(selectedGraph, (newSelectedGraph, oldSelectedGraph) => {
    const newSlug = newSelectedGraph?.slug as string | undefined;
    const oldSlug = oldSelectedGraph?.slug as string | undefined;

    if (newSlug === oldSlug) {
        return;
    }

    updateGroupGraphSlug(groupPayload, newSlug);

    for (const clause of groupPayload.clauses) {
        removeClause(groupPayload, clause);
    }
});

const isRootGroup = computed(() => {
    if (!recursionDepth) {
        return true;
    }
    return recursionDepth === 0;
});

const keyedClauses = computed(() => {
    return groupPayload.clauses.map((currentClause) => {
        return { clause: currentClause, key: useId() };
    });
});

const keyedGroups = computed(() => {
    return groupPayload.groups.map((currentGroup) => {
        return { groupPayload: currentGroup, key: useId() };
    });
});

function onToggleLogic() {
    const newLogic = groupPayload.logic === AND ? OR : AND;
    updateGroupLogic(groupPayload, newLogic);
}

function onAddSubgroup() {
    addEmptyGroup(groupPayload);
}

function onAddClause() {
    addEmptyClause(groupPayload);
}

function onRemoveChildGroup(target: GroupPayload) {
    removeGroup(groupPayload, target);
}

function onRemoveClause(target: Clause) {
    removeClause(groupPayload, target);
}

function onRemoveSelf() {
    emit("request:removeGroup", groupPayload);
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
                    v-if="
                        groupPayload.groups.length +
                            groupPayload.clauses.length >
                        1
                    "
                    :label="groupPayload.logic"
                    @click="onToggleLogic"
                />
                <Select
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

        <div v-if="selectedGraph && groupPayload.clauses.length">
            <QueryClause
                v-for="item in keyedClauses"
                :key="item.key"
                :anchor-graph="selectedGraph"
                :clause="item.clause"
                @request:remove-clause="onRemoveClause"
            />
        </div>

        <div v-if="groupPayload.groups.length">
            <QueryGroup
                v-for="item in keyedGroups"
                :key="item.key"
                :group-payload="item.groupPayload"
                :recursion-depth="(recursionDepth || 0) + 1"
                @request:remove-group-payload="onRemoveChildGroup"
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
