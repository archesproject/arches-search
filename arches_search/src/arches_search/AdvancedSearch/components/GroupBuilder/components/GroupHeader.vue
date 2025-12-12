<script setup lang="ts">
import { inject, computed, ref, watch } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Select from "primevue/select";
import Tag from "primevue/tag";

import type {
    GraphModel,
    GroupPayload,
    Node,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type RelationshipState = GroupPayload["relationship"];

type RelationshipNodeDescriptor = {
    graphSlug: string;
    nodeAlias: string;
};

type LabelledNode = Node & {
    card_x_node_x_widget_label: string;
};

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs");
const getNodesForGraphId =
    inject<(graphId: string) => Promise<LabelledNode[]>>("getNodesForGraphId");

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

const graphOptions = computed(function () {
    if (!graphs?.value) {
        return [];
    }

    return graphs.value.map(function (graphSummary) {
        return {
            label: graphSummary.name ?? graphSummary.slug,
            value: graphSummary.slug,
        };
    });
});

const currentGraphSlug = computed<string>(function () {
    return groupPayload.graph_slug;
});

const showsRelationshipToParentTag = computed<boolean>(function () {
    return !isRoot && relationshipToParent != null;
});

const relationshipToParentNodeDescriptor =
    computed<RelationshipNodeDescriptor | null>(function () {
        if (!relationshipToParent) {
            return null;
        }

        const relationshipWithPotentialPath = relationshipToParent as {
            path?: unknown;
        };

        const relationshipPath = relationshipWithPotentialPath.path;

        if (!Array.isArray(relationshipPath) || relationshipPath.length === 0) {
            return null;
        }

        const lastPathStep = relationshipPath[
            relationshipPath.length - 1
        ] as unknown;

        if (!Array.isArray(lastPathStep) || lastPathStep.length < 2) {
            return null;
        }

        const graphSlug = String(lastPathStep[0]);
        const nodeAlias = String(lastPathStep[1]);

        return {
            graphSlug,
            nodeAlias,
        };
    });

const relationshipToParentNodeIdentifier = computed<string | null>(function () {
    const descriptor = relationshipToParentNodeDescriptor.value;

    if (!descriptor) {
        return null;
    }

    return descriptor.nodeAlias;
});

const relationshipToParentGraphLabel = ref<string | null>(null);
const relationshipToParentNodeLabel = ref<string | null>(null);

watch(
    relationshipToParentNodeDescriptor,
    async function (nextNodeDescriptor) {
        relationshipToParentGraphLabel.value = null;
        relationshipToParentNodeLabel.value = null;

        if (!nextNodeDescriptor) {
            return;
        }

        if (!graphs || graphs.value.length === 0) {
            return;
        }

        const matchingGraphSummary = graphs.value.find(function (graphSummary) {
            return graphSummary.slug === nextNodeDescriptor.graphSlug;
        });

        if (matchingGraphSummary) {
            const graphLabel =
                matchingGraphSummary.name ?? matchingGraphSummary.slug ?? "";
            relationshipToParentGraphLabel.value = graphLabel || null;
        }

        if (
            !getNodesForGraphId ||
            !matchingGraphSummary ||
            !matchingGraphSummary.graphid
        ) {
            return;
        }

        try {
            const nodeSummaries = await getNodesForGraphId(
                matchingGraphSummary.graphid,
            );

            const matchingNodeSummary = nodeSummaries.find(
                function (nodeSummary) {
                    return nodeSummary.alias === nextNodeDescriptor.nodeAlias;
                },
            );

            if (!matchingNodeSummary) {
                return;
            }

            const nodeLabel =
                matchingNodeSummary.card_x_node_x_widget_label ||
                matchingNodeSummary.name ||
                matchingNodeSummary.alias;

            relationshipToParentNodeLabel.value = nodeLabel || null;
        } catch {
            relationshipToParentNodeLabel.value = null;
        }
    },
    { immediate: true },
);

const relationshipToParentPathDescription = computed<string | null>(
    function () {
        const graphLabel = relationshipToParentGraphLabel.value;
        const nodeLabel = relationshipToParentNodeLabel.value;

        if (!graphLabel && !nodeLabel) {
            return null;
        }

        if (graphLabel && nodeLabel) {
            return `${graphLabel} → ${nodeLabel}`;
        }

        return graphLabel ?? nodeLabel;
    },
);

const relationshipToParentLabel = computed<string>(function () {
    const description = relationshipToParentPathDescription.value;

    if (description) {
        return $gettext("Related via %{description}", {
            description,
        });
    }

    const nodeIdentifier = relationshipToParentNodeIdentifier.value;

    if (nodeIdentifier) {
        return $gettext("Related via %{nodeIdentifier}", {
            nodeIdentifier,
        });
    }

    return $gettext("Related via node");
});

function onSetGraphSlug(graphSlug: string): void {
    emit("change-graph", graphSlug);
}

function onRemoveGroupClick(clickEvent: MouseEvent): void {
    clickEvent.stopPropagation();
    emit("remove-group");
}
</script>

<template>
    <div class="group-header">
        <div class="group-header-row">
            <div class="group-selectors">
                <div class="group-action-text">
                    <span v-if="isRoot">
                        {{ $gettext("I want to find") }}
                    </span>
                    <Select
                        :model-value="currentGraphSlug"
                        :options="graphOptions"
                        option-label="label"
                        option-value="value"
                        :placeholder="$gettext('Select Resource')"
                        class="group-field"
                        @update:model-value="onSetGraphSlug"
                    />
                    <span v-if="isRoot">
                        {{ $gettext("resources that have...") }}
                    </span>
                </div>

                <Tag
                    v-if="showsRelationshipToParentTag"
                    class="group-indicator-pill"
                    icon="pi pi-link"
                    :value="relationshipToParentLabel"
                />
            </div>

            <div class="group-actions">
                <Button
                    v-if="!isRoot"
                    severity="danger"
                    variant="text"
                    icon="pi pi-times"
                    :aria-label="$gettext('Remove group')"
                    @click="onRemoveGroupClick"
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
    gap: 0.5rem;
    align-items: center;
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

.group-action-text {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
    font-size: 1.4rem;
}
</style>
