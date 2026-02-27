<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";
import Select from "primevue/select";
import Tag from "primevue/tag";
import type {
    GraphModel,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext, $pgettext } = useGettext();

type RelationshipState = GroupPayload["relationship"];

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs");

const { groupPayload, isRoot, relationshipToParent } = defineProps<{
    groupPayload: GroupPayload;
    isRoot?: boolean;
    relationshipToParent?: RelationshipState;
}>();

const emit = defineEmits<{
    "change-graph": [graphSlug: string];
}>();

const shouldRenderHeader = computed(() => {
    return isRoot || relationshipToParent != null;
});

const showsRelationshipTag = computed(() => {
    return !isRoot && relationshipToParent != null;
});

const graphOptions = computed(() => {
    if (!graphs?.value) {
        return [];
    }
    return graphs.value.map((graphSummary) => {
        return {
            label: graphSummary.name ?? graphSummary.slug,
            value: graphSummary.slug,
        };
    });
});

const currentGraphLabel = computed(() => {
    const matchingGraph = graphs?.value.find((graph) => {
        return graph.slug === groupPayload.graph_slug;
    });

    if (!matchingGraph?.name) {
        return $gettext("Filtering by...");
    }

    return $gettext("Filtering by: %{graphName}", {
        graphName: matchingGraph.name,
    });
});

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
                        {{
                            $pgettext(
                                "Sentence: 'I want to find [resource dropdown] resources that...'",
                                "I want to find",
                            )
                        }}
                    </span>
                    <Select
                        v-if="isRoot"
                        :model-value="groupPayload.graph_slug"
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
                        {{
                            $pgettext(
                                "Sentence: 'I want to find [resource dropdown] resources that...'",
                                "resources that...",
                            )
                        }}
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
