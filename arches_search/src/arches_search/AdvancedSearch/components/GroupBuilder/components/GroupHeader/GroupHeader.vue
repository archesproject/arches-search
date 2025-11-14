<script setup lang="ts">
import { inject, computed, ref } from "vue";

import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Button from "primevue/button";
import Tag from "primevue/tag";

import GroupAdvancedOptions from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/GroupHeader/components/GroupAdvancedOptions.vue";

import { GraphScopeToken } from "@/arches_search/AdvancedSearch/types.ts";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type GraphSummary = {
    id?: string;
    slug?: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

type RelationshipState = NonNullable<GroupPayload["relationship"]>;

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

const emit = defineEmits<{
    (event: "change-graph", graphSlug: string): void;
    (event: "change-scope", scope: GraphScopeToken): void;
    (event: "add-group"): void;
    (event: "add-clause"): void;
    (event: "add-relationship"): void;
    (event: "remove-relationship"): void;
    (
        event: "update-relationship",
        relationship: RelationshipState | null,
    ): void;
    (event: "remove-group"): void;
}>();

const { hasBodyContent, groupPayload, isRoot, hasNestedGroups } = defineProps<{
    hasBodyContent: boolean;
    groupPayload: GroupPayload;
    isRoot?: boolean;
    hasNestedGroups: boolean;
}>();

const isOptionsOpen = ref(false);

const graphOptions = computed<{ label: string; value: string }[]>(
    function getGraphOptions() {
        const availableGraphs = graphs?.value ?? [];
        const options: { label: string; value: string }[] = [];

        for (const graphSummary of availableGraphs) {
            const graphSlug = graphSummary.slug ?? "";

            if (graphSlug.length === 0) {
                continue;
            }

            const displayName =
                graphSummary.name ?? graphSummary.label ?? graphSlug;

            options.push({
                label: String(displayName),
                value: String(graphSlug),
            });
        }

        return options;
    },
);

const currentScope = computed<GraphScopeToken>(function getCurrentScope() {
    return groupPayload.scope;
});

const currentGraphSlug = computed<string>(function getCurrentGraphSlug() {
    return groupPayload.graph_slug;
});

const currentRelationship = computed<RelationshipState | null>(
    function getCurrentRelationship() {
        return groupPayload.relationship as RelationshipState | null;
    },
);

const hasRelationship = computed<boolean>(function getHasRelationship() {
    return currentRelationship.value !== null;
});

const innerGraphSlug = computed<string | undefined>(
    function getInnerGraphSlug() {
        const firstChildGroup = groupPayload.groups[0];
        return firstChildGroup?.graph_slug;
    },
);

const isTileScoped = computed<boolean>(function getIsTileScoped() {
    return currentScope.value === GraphScopeToken.TILE;
});

function onSetGraphSlug(graphSlug: string): void {
    emit("change-graph", graphSlug);
}

function onToggleOptions(event: MouseEvent): void {
    event.stopPropagation();
    isOptionsOpen.value = !isOptionsOpen.value;
}

function onAddGroupClick(event: MouseEvent): void {
    event.stopPropagation();
    emit("add-group");
}

function onAddClauseClick(event: MouseEvent): void {
    event.stopPropagation();
    emit("add-clause");
}

function onRemoveGroupClick(event: MouseEvent): void {
    event.stopPropagation();
    emit("remove-group");
}

function onChangeScope(nextScopeToken: GraphScopeToken): void {
    emit("change-scope", nextScopeToken);
}

function onAddRelationship(): void {
    emit("add-relationship");
}

function onRemoveRelationship(): void {
    emit("remove-relationship");
}

function onUpdateRelationship(
    nextRelationship: RelationshipState | null,
): void {
    emit("update-relationship", nextRelationship);
}
</script>

<template>
    <div :class="['group-header', hasBodyContent && 'group-header--spaced']">
        <div class="group-selectors">
            <Button
                class="group-gear-toggle"
                icon="pi pi-cog"
                severity="secondary"
                text
                rounded
                :aria-label="$gettext('Toggle advanced group options')"
                :aria-pressed="isOptionsOpen"
                @click="onToggleOptions"
            />
            <Select
                :model-value="currentGraphSlug"
                :options="graphOptions"
                option-label="label"
                option-value="value"
                :placeholder="$gettext('Select graph')"
                class="group-field"
                @update:model-value="onSetGraphSlug"
            />
            <div class="group-indicators">
                <Tag
                    v-if="isTileScoped"
                    class="group-indicator-pill"
                    icon="pi pi-th-large"
                    :value="$gettext('Constrained')"
                />
                <Tag
                    v-if="hasRelationship"
                    class="group-indicator-pill"
                    icon="pi pi-link"
                    :value="$gettext('Related')"
                />
            </div>
        </div>

        <div class="group-actions">
            <Button
                severity="secondary"
                icon="pi pi-plus"
                :label="$gettext('Add group')"
                @click="onAddGroupClick"
            />
            <Button
                severity="secondary"
                icon="pi pi-plus"
                :label="$gettext('Add clause')"
                @click="onAddClauseClick"
            />
            <Button
                v-if="!isRoot"
                severity="danger"
                icon="pi pi-times"
                :aria-label="$gettext('Remove group')"
                @click="onRemoveGroupClick"
            />
        </div>

        <div
            v-if="isOptionsOpen"
            class="group-advanced-row"
        >
            <GroupAdvancedOptions
                :anchor-graph-slug="currentGraphSlug"
                :has-nested-groups="hasNestedGroups"
                :has-relationship="hasRelationship"
                :inner-graph-slug="innerGraphSlug"
                :relationship="currentRelationship"
                :scope="currentScope"
                @add-relationship="onAddRelationship"
                @change-scope="onChangeScope"
                @update-relationship="onUpdateRelationship"
                @remove-relationship="onRemoveRelationship"
            />
        </div>
    </div>
</template>

<style scoped>
:deep(.p-tag-icon) {
    font-size: 1.4rem;
}

:deep(.p-tag-icon) {
    margin-bottom: 0.5rem;
    margin-inline-end: 1rem;
}

.group-header {
    display: grid;
    grid-template-columns: 1fr auto;
}

.group-header--spaced {
    margin-bottom: 1rem;
    margin-inline-start: 1.25rem;
}

.group-selectors {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
}

.group-gear-toggle {
    flex-shrink: 0;
}

.group-indicators {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-inline-start: 0.5rem;
    flex-wrap: wrap;
}

.group-indicator-pill {
    padding: 0.5rem 1rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.group-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    align-items: center;
    justify-content: flex-end;
}

.group-advanced-row {
    grid-column: 1 / -1;
    margin-top: 1rem;
    margin-inline-start: 3rem;
}
</style>
