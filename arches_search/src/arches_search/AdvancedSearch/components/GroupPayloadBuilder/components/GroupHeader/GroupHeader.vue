<script setup lang="ts">
import { defineProps, defineEmits, inject, computed, ref } from "vue";
import { useGettext } from "vue3-gettext";
import Select from "primevue/select";
import Button from "primevue/button";
import Tag from "primevue/tag";

import { GraphScopeToken } from "@/arches_search/AdvancedSearch/types.ts";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import GroupAdvancedOptions from "@/arches_search/AdvancedSearch/components/GroupPayloadBuilder/components/GroupHeader/components/GroupAdvancedOptions.vue";

const { $gettext } = useGettext();

type GraphSummary =
    | { id?: string; slug: string; name?: string; label?: string }
    | Record<string, unknown>;

type RelationshipState = NonNullable<GroupPayload["relationship"]>;

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

const props = defineProps<{
    hasBodyContent: boolean;
    graphSlug: string;
    scope: GraphScopeToken;
    isRoot?: boolean;
    hasRelationship: boolean;
    relationship: RelationshipState | null;
    innerGraphSlug?: string;
    hasNestedGroups: boolean;
}>();

const emit = defineEmits<{
    (event: "change-graph", graphSlug: string): void;
    (event: "change-scope", scope: GraphScopeToken): void;
    (event: "add-group"): void;
    (event: "add-clause"): void;
    (event: "add-relationship"): void;
    (event: "remove-relationship"): void;
    (event: "update-relationship", relationship: RelationshipState): void;
    (event: "remove-group"): void;
}>();

const isOptionsOpen = ref(false);

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

const isTileScoped = computed<boolean>(function computeIsTileScoped() {
    return props.scope === GraphScopeToken.TILE;
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

function onUpdateRelationship(nextRelationship: RelationshipState): void {
    emit("update-relationship", nextRelationship);
}
</script>

<template>
    <div
        :class="[
            'group-header',
            props.hasBodyContent && 'group-header--spaced',
        ]"
    >
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
                :model-value="props.graphSlug"
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
                    v-if="props.hasRelationship"
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
                v-if="!props.isRoot"
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
                :scope="props.scope"
                :has-nested-groups="props.hasNestedGroups"
                :has-relationship="props.hasRelationship"
                :relationship="props.relationship"
                :anchor-graph-slug="props.graphSlug"
                :inner-graph-slug="props.innerGraphSlug"
                @change-scope="onChangeScope"
                @add-relationship="onAddRelationship"
                @remove-relationship="onRemoveRelationship"
                @update-relationship="onUpdateRelationship"
            />
        </div>
    </div>
</template>

<style scoped>
:deep(.p-button-icon),
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
    font-size: 1.2rem;
}

.group-header--spaced {
    margin-bottom: 1rem;
    margin-inline-start: 0.25rem;
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

.group-field {
    min-width: 12rem;
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
    font-size: 1.2rem;
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
