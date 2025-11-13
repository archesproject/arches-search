<script setup lang="ts">
import { defineProps, defineEmits, computed } from "vue";
import { useGettext } from "vue3-gettext";
import Checkbox from "primevue/checkbox";

import { GraphScopeToken } from "@/arches_search/AdvancedSearch/types.ts";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import RelationshipEditor from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/RelationshipEditor.vue";

const { $gettext } = useGettext();

type RelationshipState = NonNullable<GroupPayload["relationship"]>;

const props = defineProps<{
    scope: GraphScopeToken;
    hasNestedGroups: boolean;
    hasRelationship: boolean;
    relationship: RelationshipState | null;
    anchorGraphSlug: string;
    innerGraphSlug?: string;
}>();

const emit = defineEmits<{
    (event: "change-scope", scope: GraphScopeToken): void;
    (event: "add-relationship"): void;
    (event: "remove-relationship"): void;
    (
        event: "update-relationship",
        relationship: RelationshipState | null,
    ): void;
}>();

const isTileScoped = computed<boolean>(function computeIsTileScoped() {
    return props.scope === GraphScopeToken.TILE;
});

function onSetScopeFromCheckbox(isChecked: boolean | undefined): void {
    const nextScopeToken =
        isChecked === true ? GraphScopeToken.TILE : GraphScopeToken.RESOURCE;
    emit("change-scope", nextScopeToken);
}

function onToggleRelationship(isChecked: boolean | undefined): void {
    if (!props.hasNestedGroups) {
        return;
    }

    if (isChecked === true && !props.hasRelationship) {
        emit("add-relationship");
    } else if (isChecked === false && props.hasRelationship) {
        emit("remove-relationship");
    }
}

function onUpdateRelationship(
    nextRelationship: RelationshipState | null,
): void {
    if (nextRelationship === null) {
        emit("remove-relationship");
        emit("update-relationship", null);
        return;
    }
    emit("update-relationship", nextRelationship);
}
</script>

<template>
    <div class="group-advanced-card">
        <div class="group-advanced-header">
            <span class="group-advanced-title">
                {{ $gettext("Advanced options") }}
            </span>
        </div>

        <div class="group-advanced-body">
            <label class="scope-checkbox-row">
                <Checkbox
                    :model-value="isTileScoped"
                    :binary="true"
                    @update:model-value="onSetScopeFromCheckbox"
                />
                <span class="scope-checkbox-label">
                    {{ $gettext("Constrain query clauses to a single tile") }}
                </span>
            </label>

            <label
                :class="[
                    'relationship-checkbox-row',
                    !props.hasNestedGroups &&
                        'relationship-checkbox-row--disabled',
                ]"
            >
                <Checkbox
                    :model-value="props.hasRelationship"
                    :binary="true"
                    :disabled="!props.hasNestedGroups"
                    @update:model-value="onToggleRelationship"
                />
                <span class="relationship-checkbox-label">
                    {{ $gettext("Define relationship to nested groups") }}
                </span>
            </label>

            <RelationshipEditor
                v-if="props.hasRelationship && props.relationship"
                class="relationship-editor-inline"
                :anchor-graph-slug="props.anchorGraphSlug"
                :inner-graph-slug="props.innerGraphSlug"
                :relationship="props.relationship as RelationshipState"
                @update:relationship="onUpdateRelationship"
            />
        </div>
    </div>
</template>

<style scoped>
.group-advanced-card {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
    border-radius: 0.75rem;
    border: 0.0625rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    font-size: 1.2rem;
}

.group-advanced-header {
    display: flex;
    align-items: center;
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 0.0625rem solid var(--p-content-border-color);
}

.group-advanced-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--p-text-color-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.group-advanced-body {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.scope-checkbox-row {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.2rem;
    cursor: pointer;
}

.scope-checkbox-label {
    user-select: none;
    cursor: pointer;
}

.relationship-checkbox-row {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.2rem;
    cursor: pointer;
}

.relationship-checkbox-row--disabled {
    opacity: 0.6;
    cursor: default;
}

.relationship-checkbox-label {
    user-select: none;
    cursor: pointer;
}

.relationship-editor-inline {
    width: 100%;
}
</style>
