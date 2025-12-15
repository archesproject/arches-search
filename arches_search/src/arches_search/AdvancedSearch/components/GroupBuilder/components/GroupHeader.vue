<script setup lang="ts">
import { inject, computed } from "vue";

import { useGettext } from "vue3-gettext";

import Select from "primevue/select";
import Tag from "primevue/tag";

import type {
    GraphModel,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type RelationshipState = GroupPayload["relationship"];

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs");

const emit = defineEmits<{
    (event: "change-graph", graphSlug: string): void;
    (event: "add-group"): void;
    (event: "add-clause"): void;
    (event: "add-relationship"): void;
    (event: "remove-relationship"): void;
    (event: "update-relationship", relationship: RelationshipState): void;
    (event: "remove-group"): void;
}>();

const { groupPayload, isRoot, relationshipToParent } = defineProps<{
    groupPayload: GroupPayload;
    isRoot?: boolean;
    relationshipToParent?: RelationshipState;
}>();

const shouldRenderHeader = computed<boolean>(function getShouldRenderHeader() {
    return Boolean(isRoot) || relationshipToParent != null;
});

const graphOptions = computed(function getGraphOptions() {
    if (!graphs?.value) {
        return [];
    }

    return graphs.value.map(function mapGraphOption(graphSummary) {
        return {
            label: graphSummary.name ?? graphSummary.slug,
            value: graphSummary.slug,
        };
    });
});

const currentGraphSlug = computed<string>(function getCurrentGraphSlug() {
    return groupPayload.graph_slug;
});

const currentGraphLabel = computed<string>(function getCurrentGraphLabel() {
    const graphSlug = currentGraphSlug.value;

    if (!graphs?.value || graphs.value.length === 0) {
        return graphSlug;
    }

    const matchingGraphSummary = graphs.value.find(
        function findMatchingGraphSummary(graphSummary) {
            return graphSummary.slug === graphSlug;
        },
    );

    return (
        matchingGraphSummary?.name ?? matchingGraphSummary?.slug ?? graphSlug
    );
});

const showsRelationshipTag = computed<boolean>(
    function getShowsRelationshipTag() {
        return !isRoot && relationshipToParent != null;
    },
);

function onSetGraphSlug(graphSlug: string): void {
    emit("change-graph", graphSlug);
}
</script>

<template>
    <div
        v-if="shouldRenderHeader"
        class="group-header"
        :style="{
            marginBottom: isRoot ? '1rem' : '1.5rem',
        }"
    >
        <div class="group-header-row">
            <div class="group-selectors">
                <div class="group-action-text">
                    <span v-if="isRoot">
                        {{ $gettext("I want to find") }}
                    </span>
                    <Select
                        v-if="isRoot"
                        :model-value="currentGraphSlug"
                        :options="graphOptions"
                        option-label="label"
                        option-value="value"
                        :placeholder="$gettext('Select Resource')"
                        class="group-field"
                        filter
                        :filter-placeholder="$gettext('Filter resource models')"
                        @update:model-value="onSetGraphSlug"
                    />
                    <span v-if="isRoot">
                        {{ $gettext("resources that have...") }}
                    </span>
                </div>

                <Tag
                    v-if="showsRelationshipTag"
                    class="group-indicator-pill"
                    icon="pi pi-link"
                    :value="currentGraphLabel"
                />
            </div>
        </div>
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
}

.group-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
}

.group-selectors {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
}

.group-indicator-pill {
    padding: 0.5rem 1rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.group-action-text {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
    font-size: 1.4rem;
}
</style>
