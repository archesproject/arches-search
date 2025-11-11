<script setup lang="ts">
import {
    defineProps,
    defineEmits,
    inject,
    ref,
    computed,
    watch,
    nextTick,
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
    makeEmptyGroupPayload,
    makeEmptyLiteralClause,
    makeEmptyRelationshipBlock,
    type GroupPayload,
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

const localGroup = ref<GroupPayload>(makeEmptyGroupPayload());
const isSyncingFromProp = ref(false);

/* Stable keys for dynamic lists */
const childGroupKeys = ref<string[]>([]);
const clauseKeys = ref<string[]>([]);

function createId(): string {
    return globalThis.crypto.randomUUID();
}

/* Only watch identity changes from parent; no deep traversal here */
watch(
    () => props.modelValue,
    async (incoming) => {
        isSyncingFromProp.value = true;

        /* Assign incoming directly (no deep clone); the parent owns v-model */
        localGroup.value = incoming ?? makeEmptyGroupPayload();

        /* Rebuild keys to match incoming lengths once per identity change */
        childGroupKeys.value = Array.from(
            { length: localGroup.value.groups.length },
            () => createId(),
        );
        clauseKeys.value = Array.from(
            { length: localGroup.value.clauses.length },
            () => createId(),
        );

        await nextTick();
        isSyncingFromProp.value = false;
    },
    { immediate: true },
);

/* Deep watch to propagate edits, but emit the same object (no clone) */
watch(
    localGroup,
    (nextValue) => {
        if (isSyncingFromProp.value) return;
        emit("update:modelValue", nextValue);
    },
    { deep: true },
);

const scopeOptions = computed(() => [
    { label: $gettext("Resource"), value: GraphScopeToken.RESOURCE },
    { label: $gettext("Tile"), value: GraphScopeToken.TILE },
]);

const logicOptions = computed(() => [
    { label: $gettext("AND"), value: LogicToken.AND },
    { label: $gettext("OR"), value: LogicToken.OR },
]);

const graphOptions = computed(() => {
    const graphList = graphs?.value ?? [];
    return graphList
        .map((graphEntry: GraphSummary) => {
            const slug = (graphEntry as { slug?: string }).slug ?? "";
            const displayName =
                (graphEntry as { name?: string }).name ??
                (graphEntry as { label?: string }).label ??
                slug;
            return { label: String(displayName), value: String(slug) };
        })
        .filter((option) => option.value.length > 0);
});

/* --- actions --- */

function addGroup(): void {
    const childGroup: GroupPayload = {
        ...makeEmptyGroupPayload(),
        graph_slug: localGroup.value.graph_slug,
        scope: localGroup.value.scope,
    };
    localGroup.value = {
        ...localGroup.value,
        groups: [...localGroup.value.groups, childGroup],
    };
    childGroupKeys.value = [...childGroupKeys.value, createId()];
}

function removeGroupAtIndex(childIndex: number): void {
    const nextGroups = localGroup.value.groups.slice();
    nextGroups.splice(childIndex, 1);
    localGroup.value = { ...localGroup.value, groups: nextGroups };

    const nextKeys = childGroupKeys.value.slice();
    nextKeys.splice(childIndex, 1);
    childGroupKeys.value = nextKeys;
}

function addClause(): void {
    const nextClauses = localGroup.value.clauses.slice();
    nextClauses.push(makeEmptyLiteralClause());
    localGroup.value = { ...localGroup.value, clauses: nextClauses };

    clauseKeys.value = [...clauseKeys.value, createId()];
}

function removeClauseAtIndex(clauseIndex: number): void {
    const nextClauses = localGroup.value.clauses.slice();
    nextClauses.splice(clauseIndex, 1);
    localGroup.value = { ...localGroup.value, clauses: nextClauses };

    const nextKeys = clauseKeys.value.slice();
    nextKeys.splice(clauseIndex, 1);
    clauseKeys.value = nextKeys;
}

function addRelationship(): void {
    if (localGroup.value.relationship !== null) return;
    localGroup.value = {
        ...localGroup.value,
        relationship: makeEmptyRelationshipBlock(),
    };
}

function removeRelationship(): void {
    if (localGroup.value.relationship === null) return;
    localGroup.value = { ...localGroup.value, relationship: null };
}
</script>

<template>
    <Card class="group-card">
        <template #title>
            <div class="group-header">
                <div class="row">
                    <Select
                        v-model="localGroup.graph_slug"
                        :options="graphOptions"
                        option-label="label"
                        option-value="value"
                        :placeholder="$gettext('Select graph')"
                        class="field"
                    />
                    <Select
                        v-model="localGroup.scope"
                        :options="scopeOptions"
                        option-label="label"
                        option-value="value"
                        class="field"
                    />
                    <Select
                        v-model="localGroup.logic"
                        :options="logicOptions"
                        option-label="label"
                        option-value="value"
                        class="field"
                    />
                </div>

                <div class="actions">
                    <Button
                        severity="secondary"
                        icon="pi pi-plus"
                        :label="$gettext('Add group')"
                        @click="addGroup"
                    />
                    <Button
                        severity="secondary"
                        icon="pi pi-plus"
                        :label="$gettext('Add clause')"
                        @click="addClause"
                    />
                    <Button
                        v-if="localGroup.relationship === null"
                        severity="secondary"
                        icon="pi pi-link"
                        :label="$gettext('Add relationship')"
                        @click="addRelationship"
                    />
                    <Button
                        v-else
                        severity="danger"
                        icon="pi pi-unlink"
                        :label="$gettext('Remove relationship')"
                        @click="removeRelationship"
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
            <div class="body">
                <div
                    v-if="localGroup.clauses.length > 0"
                    class="clauses"
                >
                    <div
                        v-for="(
                            _clausePayload, clauseIndex
                        ) in localGroup.clauses"
                        :key="clauseKeys[clauseIndex]"
                        class="clause-row"
                    >
                        <span
                            >{{ $gettext("Clause") }}
                            {{ clauseIndex + 1 }}</span
                        >
                        <Button
                            severity="danger"
                            icon="pi pi-trash"
                            :label="$gettext('Remove clause')"
                            @click="removeClauseAtIndex(clauseIndex)"
                        />
                    </div>
                    <Divider />
                </div>

                <div
                    v-if="localGroup.groups.length > 0"
                    class="children"
                >
                    <GroupPayloadBuilder
                        v-for="(
                            childGroupPayload, childIndex
                        ) in localGroup.groups"
                        :key="childGroupKeys[childIndex]"
                        v-model="localGroup.groups[childIndex]"
                        @remove="removeGroupAtIndex(childIndex)"
                    />
                </div>
            </div>
        </template>
    </Card>
</template>

<style scoped>
.group-card {
    margin-bottom: 1rem;
}
.group-header {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0.75rem;
    align-items: center;
}
.row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
}
.actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}
.body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
.field {
    min-width: 12rem;
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
.children {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}
</style>
