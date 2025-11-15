<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Checkbox from "primevue/checkbox";

import RelationshipEditor from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/RelationshipEditor.vue";

import { GraphScopeToken } from "@/arches_search/AdvancedSearch/types.ts";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type RelationshipState = NonNullable<GroupPayload["relationship"]>;

const {
    scope,
    hasNestedGroups,
    hasRelationship,
    relationship,
    anchorGraphSlug,
    innerGraphSlug,
} = defineProps<{
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

const isTileScoped = computed<boolean>(function getIsTileScoped() {
    return scope === GraphScopeToken.TILE;
});

const isRelationshipCheckboxDisabled = computed<boolean>(
    function getIsRelationshipCheckboxDisabled() {
        return !hasNestedGroups;
    },
);

const relationshipCheckboxRowClasses = computed<string[]>(
    function getRelationshipCheckboxRowClasses() {
        const classes = ["relationship-checkbox-row"];
        if (isRelationshipCheckboxDisabled.value) {
            classes.push("relationship-checkbox-row--disabled");
        }
        return classes;
    },
);

const shouldShowRelationshipEditor = computed<boolean>(
    function getShouldShowRelationshipEditor() {
        return hasRelationship && relationship !== null;
    },
);

function onSetScopeFromCheckbox(isChecked: boolean | undefined): void {
    const nextScopeToken =
        isChecked === true ? GraphScopeToken.TILE : GraphScopeToken.RESOURCE;
    emit("change-scope", nextScopeToken);
}

function onToggleRelationship(isChecked: boolean | undefined): void {
    if (!hasNestedGroups) {
        return;
    }

    if (isChecked === true && !hasRelationship) {
        emit("add-relationship");
        return;
    }

    if (isChecked === false && hasRelationship) {
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

            <label :class="relationshipCheckboxRowClasses">
                <Checkbox
                    :model-value="hasRelationship"
                    :binary="true"
                    :disabled="isRelationshipCheckboxDisabled"
                    @update:model-value="onToggleRelationship"
                />
                <span class="relationship-checkbox-label">
                    {{ $gettext("Define relationship to nested groups") }}
                </span>
            </label>

            <RelationshipEditor
                v-if="shouldShowRelationshipEditor"
                class="relationship-editor-inline"
                :anchor-graph-slug="anchorGraphSlug"
                :inner-graph-slug="innerGraphSlug"
                :relationship="relationship as RelationshipState"
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
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
}

.group-advanced-header {
    display: flex;
    align-items: center;
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.group-advanced-title {
    color: var(--p-text-color-secondary);
    text-transform: uppercase;
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
    cursor: pointer;
}

.relationship-checkbox-row--disabled {
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
