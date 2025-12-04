<script setup lang="ts">
import { inject, computed } from "vue";

import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Button from "primevue/button";
import Tag from "primevue/tag";

import RelationshipEditor from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/RelationshipEditor.vue";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type GraphSummary = {
    id?: string;
    slug: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

type GraphOption = {
    label: string;
    value: string;
};

type RelationshipState = NonNullable<GroupPayload["relationship"]>;

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

const emit = defineEmits<{
    (event: "change-graph", graphSlug: string): void;
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

const {
    groupPayload,
    isRoot,
    hasNestedGroups,
    shouldIndent,
    relationshipToParent,
} = defineProps<{
    groupPayload: GroupPayload;
    isRoot?: boolean;
    hasNestedGroups: boolean;
    shouldIndent: boolean;
    relationshipToParent?: RelationshipState | null;
}>();

const graphOptions = computed<GraphOption[]>(function () {
    return (
        graphs?.value.map(function (graphSummary) {
            return {
                label: graphSummary.name ?? graphSummary.slug,
                value: graphSummary.slug,
            };
        }) ?? []
    );
});

const currentGraphSlug = computed<string>(function () {
    return groupPayload.graph_slug;
});

const isGraphSelected = computed<boolean>(function () {
    return currentGraphSlug.value.trim().length > 0;
});

const currentRelationship = computed<RelationshipState | null>(function () {
    return groupPayload.relationship as RelationshipState | null;
});

const hasRelationship = computed<boolean>(function () {
    return currentRelationship.value !== null;
});

const innerGraphSlug = computed<string | undefined>(function () {
    const firstChildGroup = groupPayload.groups[0];
    return firstChildGroup?.graph_slug;
});

const relateButtonTitle = computed<string>(function () {
    if (!isGraphSelected.value) {
        return $gettext("Select what this group filters before relating.");
    }

    if (!hasNestedGroups) {
        return $gettext("Add a nested group below to enable relationships.");
    }

    if (hasRelationship.value) {
        return $gettext("This group is already related to its nested group.");
    }

    return $gettext("Relate this group to its nested group.");
});

const showsRelationshipToParentTag = computed<boolean>(function () {
    return !isRoot && relationshipToParent != null;
});

const relationshipToParentNodeIdentifier = computed<string | null>(function () {
    if (!relationshipToParent) {
        return null;
    }

    const unsafeRelationship = relationshipToParent as unknown as {
        path?: unknown;
    };

    const relationshipPath = unsafeRelationship.path;

    if (!Array.isArray(relationshipPath) || relationshipPath.length === 0) {
        return null;
    }

    const lastPathStep = relationshipPath[
        relationshipPath.length - 1
    ] as unknown;

    if (!Array.isArray(lastPathStep) || lastPathStep.length < 2) {
        return null;
    }

    const unsafeNodeIdentifier = lastPathStep[1] as unknown;

    if (
        typeof unsafeNodeIdentifier !== "string" ||
        unsafeNodeIdentifier.trim().length === 0
    ) {
        return null;
    }

    return unsafeNodeIdentifier;
});

const relationshipToParentLabel = computed<string>(function () {
    const nodeIdentifier = relationshipToParentNodeIdentifier.value;

    if (nodeIdentifier) {
        return $gettext("Related to parent via %{nodeIdentifier}", {
            nodeIdentifier,
        });
    }

    return $gettext("Related to parent via node");
});

function onSetGraphSlug(graphSlug: string): void {
    emit("change-graph", graphSlug);
}

function onAddGroupClick(clickEvent: MouseEvent): void {
    clickEvent.stopPropagation();
    emit("add-group");
}

function onAddClauseClick(clickEvent: MouseEvent): void {
    clickEvent.stopPropagation();
    emit("add-clause");
}

function onRemoveGroupClick(clickEvent: MouseEvent): void {
    clickEvent.stopPropagation();
    emit("remove-group");
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
    if (nextRelationship === null) {
        onClearRelationship(new MouseEvent("click"));
        return;
    }

    emit("update-relationship", nextRelationship);
}

function onRelationshipButtonClick(clickEvent: MouseEvent): void {
    clickEvent.stopPropagation();

    if (!hasNestedGroups || hasRelationship.value) {
        return;
    }

    onAddRelationship();
}

function onClearRelationship(clickEvent?: MouseEvent): void {
    if (clickEvent) {
        clickEvent.stopPropagation();
    }
    emit("update-relationship", null);
    onRemoveRelationship();
}
</script>

<template>
    <div :class="['group-header', shouldIndent && 'group-header--spaced']">
        <div class="group-header-row">
            <div class="group-selectors">
                <Select
                    :model-value="currentGraphSlug"
                    :options="graphOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="$gettext('Select what to filter')"
                    class="group-field"
                    @update:model-value="onSetGraphSlug"
                />

                <div class="group-indicators">
                    <Tag
                        v-if="showsRelationshipToParentTag"
                        class="group-indicator-pill"
                        icon="pi pi-link"
                        :value="relationshipToParentLabel"
                    />
                </div>

                <Button
                    v-if="!hasRelationship"
                    class="group-relate-button"
                    severity="secondary"
                    icon="pi pi-link"
                    :label="$gettext('Relate to nested groups')"
                    :title="relateButtonTitle"
                    :disabled="
                        !isGraphSelected || !hasNestedGroups || hasRelationship
                    "
                    @click="onRelationshipButtonClick"
                />
            </div>

            <div class="group-actions">
                <Button
                    severity="secondary"
                    icon="pi pi-plus"
                    :label="$gettext('Add group')"
                    :disabled="!isGraphSelected"
                    @click="onAddGroupClick"
                />
                <Button
                    severity="secondary"
                    icon="pi pi-plus"
                    :label="$gettext('Add filter')"
                    :disabled="!isGraphSelected"
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
        </div>

        <RelationshipEditor
            v-if="hasRelationship"
            class="relationship-editor-inline"
            :anchor-graph-slug="currentGraphSlug"
            :inner-graph-slug="innerGraphSlug"
            :is-root="isRoot"
            :relationship="currentRelationship as RelationshipState"
            @update:relationship="onUpdateRelationship"
        />
    </div>
</template>

<style scoped>
:deep(.p-tag-icon) {
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
    margin-inline-end: 1rem;
}

.group-header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.group-header--spaced {
    margin-inline-start: 0.25rem;
}

.group-header-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
}

.group-selectors {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
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
    flex-shrink: 0;
}

.relationship-editor-inline {
    align-self: stretch;
}
</style>
