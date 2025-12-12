<script setup lang="ts">
import { computed, watch, ref, inject } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Select from "primevue/select";
import Card from "primevue/card";
import Message from "primevue/message";

import PathBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/PathBuilder.vue";

import type {
    GroupPayload,
    GraphModel,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type RelationshipState = NonNullable<GroupPayload["relationship"]>;
type TraversalQuantifier = RelationshipState["traversal_quantifiers"][number];

type RelationshipPathSequence = readonly (readonly [string, string])[];

const TRAVERSAL_QUANTIFIER_ANY = "ANY";
const TRAVERSAL_QUANTIFIER_ALL = "ALL";
const TRAVERSAL_QUANTIFIER_NONE = "NONE";

const emit = defineEmits<{
    (event: "update:relationship", value: RelationshipState | null): void;
}>();

const { relationship, anchorGraphSlug, innerGraphSlug, isRoot } = defineProps<{
    relationship: RelationshipState;
    anchorGraphSlug: string;
    innerGraphSlug: string;
    isRoot?: boolean;
}>();

const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs")!;

const hasCompatibleRelationshipNodes = ref(true);

const hasSelectedRelationshipPath = computed<boolean>(() => {
    return relationship.path.some((segment) => {
        const selectedNodeAlias = String(segment?.[1] ?? "").trim();
        return selectedNodeAlias.length > 0;
    });
});

const traversalQuantifierOptions = computed<{ label: string; value: string }[]>(
    () => {
        return [
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
        ];
    },
);

const currentTraversalQuantifier = computed<string>(() => {
    const firstQuantifier = relationship.traversal_quantifiers[0];
    if (!firstQuantifier) {
        return TRAVERSAL_QUANTIFIER_ANY;
    }
    return firstQuantifier;
});

const graphSlugsForPathBuilder = computed<string[]>(() => {
    const graphSlugs: string[] = [];

    if (anchorGraphSlug) {
        graphSlugs.push(anchorGraphSlug);
    }

    if (innerGraphSlug && innerGraphSlug !== anchorGraphSlug) {
        graphSlugs.push(innerGraphSlug);
    }

    return graphSlugs;
});

const anchorGraphName = computed<string>(() => {
    return graphs.value.find(
        (graphModel) => graphModel.slug === anchorGraphSlug,
    )!.name;
});

const innerGraphName = computed<string>(() => {
    return graphs.value.find(
        (graphModel) => graphModel.slug === innerGraphSlug,
    )!.name;
});

const relationshipLeadinText = computed<string>(() => {
    return $gettext("Related %{outer} to %{inner} by", {
        outer: anchorGraphName.value,
        inner: innerGraphName.value,
    });
});

watch(
    () => innerGraphSlug,
    (
        nextInnerGraphSlug: string | undefined,
        previousInnerGraphSlug: string | undefined,
    ) => {
        if (!previousInnerGraphSlug || !nextInnerGraphSlug) {
            return;
        }

        if (nextInnerGraphSlug === previousInnerGraphSlug) {
            return;
        }

        emit("update:relationship", null);
    },
);

function onChangeTraversalQuantifier(nextQuantifierRaw: string): void {
    const normalizedQuantifier = String(nextQuantifierRaw).toUpperCase();

    let safeQuantifierString = TRAVERSAL_QUANTIFIER_ANY;

    if (normalizedQuantifier === TRAVERSAL_QUANTIFIER_ALL) {
        safeQuantifierString = TRAVERSAL_QUANTIFIER_ALL;
    } else if (normalizedQuantifier === TRAVERSAL_QUANTIFIER_NONE) {
        safeQuantifierString = TRAVERSAL_QUANTIFIER_NONE;
    }

    const safeQuantifier = safeQuantifierString as TraversalQuantifier;

    const updatedRelationship: RelationshipState = {
        ...relationship,
        traversal_quantifiers: [safeQuantifier],
    };

    emit("update:relationship", updatedRelationship);
}

function deriveIsInverseFromPathSequence(
    nextPathSequence: RelationshipPathSequence,
): boolean {
    if (!anchorGraphSlug || !innerGraphSlug) {
        return relationship.is_inverse;
    }

    if (anchorGraphSlug === innerGraphSlug) {
        return relationship.is_inverse;
    }

    const firstSegment = nextPathSequence[0];

    if (!firstSegment) {
        return relationship.is_inverse;
    }

    const firstGraphSlug = firstSegment[0];

    if (firstGraphSlug === innerGraphSlug) {
        return true;
    }

    if (firstGraphSlug === anchorGraphSlug) {
        return false;
    }

    return relationship.is_inverse;
}

function onUpdatePathSequence(
    nextPathSequence: RelationshipPathSequence,
): void {
    const nextPath = nextPathSequence.map((segment) => {
        return [segment[0], segment[1]] as [string, string];
    });

    const nextIsInverse = deriveIsInverseFromPathSequence(nextPathSequence);

    const updatedRelationship: RelationshipState = {
        ...relationship,
        path: nextPath,
        is_inverse: nextIsInverse,
    };

    emit("update:relationship", updatedRelationship);
}

function onCompatibleRelationshipNodesChanged(
    nextHasCompatibleRelationshipNodes: boolean,
): void {
    hasCompatibleRelationshipNodes.value = nextHasCompatibleRelationshipNodes;
}

function onCloseClick(): void {
    emit("update:relationship", null);
}
</script>

<template>
    <Card
        class="relationship-card"
        :style="{
            marginInlineEnd: isRoot ? 0 : '3rem',
        }"
    >
        <template #content>
            <div class="relationship-inline-row">
                <span class="relationship-leadin-text">
                    {{ relationshipLeadinText }}
                </span>

                <PathBuilder
                    v-if="graphSlugsForPathBuilder.length > 0"
                    v-show="hasCompatibleRelationshipNodes"
                    :graph-slugs="graphSlugsForPathBuilder"
                    :relationship-between-graphs="graphSlugsForPathBuilder"
                    :path-sequence="relationship.path"
                    :should-prepend-graph-name="true"
                    @update:path-sequence="onUpdatePathSequence"
                    @compatible-relationship-nodes-changed="
                        onCompatibleRelationshipNodesChanged
                    "
                />

                <Select
                    v-if="
                        hasCompatibleRelationshipNodes &&
                        hasSelectedRelationshipPath
                    "
                    :model-value="currentTraversalQuantifier"
                    :options="traversalQuantifierOptions"
                    option-label="label"
                    option-value="value"
                    class="relationship-quantifier-select"
                    :placeholder="$gettext('Match requirement')"
                    :aria-label="$gettext('Relationship match requirement')"
                    :title="
                        $gettext(
                            'Decide how many related records must match for this relationship to be considered true.',
                        )
                    "
                    @update:model-value="onChangeTraversalQuantifier"
                />

                <Message
                    v-if="!hasCompatibleRelationshipNodes"
                    severity="error"
                    class="relationship-error-message"
                >
                    {{
                        $gettext(
                            "No compatible relationship nodes exist between the selected graphs.",
                        )
                    }}
                </Message>

                <Button
                    variant="text"
                    severity="danger"
                    icon="pi pi-times"
                    class="relationship-inline-close"
                    :aria-label="$gettext('Remove relationship')"
                    @click="onCloseClick"
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
    margin-top: 1rem;
}

.relationship-inline-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    font-size: 1.2rem;
}

.relationship-leadin-text {
    font-weight: 600;
}

.relationship-inline-close {
    margin-inline-start: auto;
}

.relationship-error-message {
    flex: 1 1 auto;
}
</style>
