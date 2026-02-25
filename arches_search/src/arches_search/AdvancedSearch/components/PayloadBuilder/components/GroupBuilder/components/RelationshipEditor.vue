<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Card from "primevue/card";
import Message from "primevue/message";
import Select from "primevue/select";

import PathBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/PathBuilder.vue";

import type {
    GraphModel,
    RelationshipBlock,
    RelationshipPath,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext, $pgettext } = useGettext();

const TRAVERSAL_QUANTIFIER_ANY = "ANY";
const TRAVERSAL_QUANTIFIER_ALL = "ALL";
const TRAVERSAL_QUANTIFIER_NONE = "NONE";

const emit = defineEmits<{
    "update:relationship": [RelationshipBlock | null];
    "update:innerGraphSlug": [string];
}>();

const { relationship, anchorGraphSlug, innerGraphSlug } = defineProps<{
    relationship: RelationshipBlock;
    anchorGraphSlug: string;
    innerGraphSlug: string;
}>();

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;
const getRelatableNodesTreeForGraphId = inject<
    (graphId: string) => Promise<{ relatable_graphs: GraphModel[] }>
>("getRelatableNodesTreeForGraphId")!;

const isLoadingRelatableTree = ref(false);
const relatableTreeError = ref<Error | null>(null);

const relatableNodesTree = ref<{
    relatable_graphs: GraphModel[];
} | null>(null);

const anchorGraph = computed(() => {
    return graphs.value.find(
        (graphModel) => graphModel.slug === anchorGraphSlug,
    );
});

const tagText = computed(() => {
    const name = anchorGraph.value?.name;

    if (name) {
        return $gettext("Relate %{name} to", { name });
    }
    return $gettext("Relate to");
});

const relatableGraphOptions = computed(() =>
    (relatableNodesTree.value?.relatable_graphs ?? [])
        .map((graph) => ({ label: graph.name, value: graph.slug }))
        .sort((left, right) => left.label.localeCompare(right.label)),
);

const traversalQuantifierOptions = computed(() => [
    {
        label: $gettext("At least one related record must match"),
        value: TRAVERSAL_QUANTIFIER_ANY,
    },
    {
        label: $gettext("Every related record must match"),
        value: TRAVERSAL_QUANTIFIER_ALL,
    },
    {
        label: $gettext("No related records match"),
        value: TRAVERSAL_QUANTIFIER_NONE,
    },
]);

const currentTraversalQuantifier = computed(() => {
    return relationship.traversal_quantifiers[0] ?? TRAVERSAL_QUANTIFIER_ANY;
});

const pathSequenceForPathBuilder = computed(() => {
    return relationship.path.slice(0, 1);
});

watch(
    () => anchorGraphSlug,
    async (_next, previousSlug) => {
        if (previousSlug) {
            if (innerGraphSlug) {
                emit("update:innerGraphSlug", "");
            }
            if (relationship.path.length > 0) {
                emit("update:relationship", { ...relationship, path: [] });
            }
        }
        await loadRelatableTree();
    },
    { immediate: true },
);

watch(
    () => innerGraphSlug,
    (_next, previousSlug) => {
        if (!previousSlug) {
            return;
        }
        emit("update:relationship", { ...relationship, path: [] });
    },
);

async function loadRelatableTree() {
    isLoadingRelatableTree.value = true;
    relatableTreeError.value = null;

    const graphId = anchorGraph.value?.graphid;

    if (!graphId) {
        relatableNodesTree.value = null;
        isLoadingRelatableTree.value = false;
        return;
    }

    try {
        relatableNodesTree.value =
            await getRelatableNodesTreeForGraphId(graphId);

        const options = relatableGraphOptions.value;

        if (!innerGraphSlug) {
            if (options.length === 1) {
                emit("update:innerGraphSlug", options[0]!.value);
            }
        } else if (!options.some((option) => option.value === innerGraphSlug)) {
            emit("update:innerGraphSlug", "");

            if (relationship.path.length > 0) {
                emit("update:relationship", { ...relationship, path: [] });
            }
        }
    } catch (error) {
        relatableTreeError.value = error as Error;
        relatableNodesTree.value = null;
    } finally {
        isLoadingRelatableTree.value = false;
    }
}

function onUpdatePathSequence(nextPathSequence: RelationshipPath): void {
    if (nextPathSequence.length === 0) {
        emit("update:relationship", { ...relationship, path: [] });
        return;
    }
    const [firstGraphSlug, firstNodeAlias] = nextPathSequence[0]!;
    emit("update:relationship", {
        ...relationship,
        path: [[firstGraphSlug, firstNodeAlias]],
        is_inverse: firstGraphSlug !== anchorGraphSlug,
    });
}

function onChangeTraversalQuantifier(nextQuantifier: string): void {
    emit("update:relationship", {
        ...relationship,
        traversal_quantifiers: [
            nextQuantifier,
        ] as RelationshipBlock["traversal_quantifiers"],
    });
}
</script>

<template>
    <Card class="relationship-card">
        <template #content>
            <Message
                v-if="relatableTreeError"
                severity="error"
                class="relationship-message"
            >
                {{ relatableTreeError.message }}
            </Message>

            <div
                v-else
                class="relationship-inline-row"
            >
                <span class="relationship-leadin-text">
                    {{ tagText }}
                </span>

                <Select
                    v-if="relatableGraphOptions.length > 0"
                    :model-value="innerGraphSlug"
                    :options="relatableGraphOptions"
                    :filter="true"
                    option-label="label"
                    option-value="value"
                    class="relationship-related-graph-select"
                    :disabled="isLoadingRelatableTree"
                    :placeholder="$gettext('Related record type')"
                    :aria-label="$gettext('Related record type')"
                    @update:model-value="emit('update:innerGraphSlug', $event)"
                />

                <span
                    v-if="innerGraphSlug"
                    class="relationship-leadin-text"
                >
                    {{
                        $pgettext(
                            'relationship editor: "Relate [type] to [type] via [field] and [quantifier]"',
                            "via",
                        )
                    }}
                </span>

                <div
                    v-if="innerGraphSlug"
                    class="relationship-path-builder"
                >
                    <PathBuilder
                        :graph-slugs="[anchorGraphSlug, innerGraphSlug]"
                        :path-sequence="pathSequenceForPathBuilder"
                        :restrict-to-resource-instance-datatypes="true"
                        :relationship-between-graphs="[
                            anchorGraphSlug,
                            innerGraphSlug,
                        ]"
                        :should-prepend-graph-name="true"
                        @update:path-sequence="onUpdatePathSequence"
                    />
                </div>

                <span
                    v-if="innerGraphSlug && relationship.path.length > 0"
                    class="relationship-leadin-text"
                >
                    {{
                        $pgettext(
                            'relationship editor: "Relate [type] to [type] via [field] and [quantifier]"',
                            "and",
                        )
                    }}
                </span>

                <Select
                    v-if="innerGraphSlug && relationship.path.length > 0"
                    :model-value="currentTraversalQuantifier"
                    :options="traversalQuantifierOptions"
                    option-label="label"
                    option-value="value"
                    class="relationship-quantifier-select"
                    :placeholder="$gettext('Match requirement')"
                    :aria-label="$gettext('Relationship match requirement')"
                    @update:model-value="onChangeTraversalQuantifier"
                />
            </div>
        </template>
    </Card>
</template>

<style scoped>
.relationship-card {
    font-size: 1.2rem;
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
}

.relationship-inline-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.relationship-leadin-text {
    font-weight: 600;
}

.relationship-path-builder {
    display: flex;
}

.relationship-message {
    flex: 1 1 auto;
}
</style>
