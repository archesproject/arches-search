<script setup lang="ts">
import { computed, watch, ref } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Card from "primevue/card";
import Message from "primevue/message";

import PathBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/PathBuilder.vue";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type RelationshipState = NonNullable<GroupPayload["relationship"]>;
type TraversalQuantifier = RelationshipState["traversal_quantifiers"][number];

type RelationshipDirection = "OUTER_TO_NESTED" | "NESTED_TO_OUTER";

type RelationshipDirectionOption = {
    label: string;
    value: RelationshipDirection;
};

type RelationshipPathSequence = readonly (readonly [string, string])[];

const TRAVERSAL_QUANTIFIER_ANY = "ANY";
const TRAVERSAL_QUANTIFIER_ALL = "ALL";
const TRAVERSAL_QUANTIFIER_NONE = "NONE";

const RELATIONSHIP_DIRECTION_OUTER_TO_NESTED: RelationshipDirection =
    "OUTER_TO_NESTED";
const RELATIONSHIP_DIRECTION_NESTED_TO_OUTER: RelationshipDirection =
    "NESTED_TO_OUTER";

const emit = defineEmits<{
    (event: "update:relationship", value: RelationshipState | null): void;
}>();

const { relationship, anchorGraphSlug, innerGraphSlug, isRoot } = defineProps<{
    relationship: RelationshipState;
    anchorGraphSlug: string;
    innerGraphSlug: string;
    isRoot?: boolean;
}>();

const hasCompatibleRelationshipNodes = ref(true);

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

const relationshipDirectionOptions = computed<RelationshipDirectionOption[]>(
    () => {
        return [
            {
                label: $gettext("Outer group → Nested groups"),
                value: RELATIONSHIP_DIRECTION_OUTER_TO_NESTED,
            },
            {
                label: $gettext("Nested groups → Outer group"),
                value: RELATIONSHIP_DIRECTION_NESTED_TO_OUTER,
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

const currentRelationshipDirection = computed<string>(() => {
    if (relationship.is_inverse) {
        return RELATIONSHIP_DIRECTION_NESTED_TO_OUTER;
    }
    return RELATIONSHIP_DIRECTION_OUTER_TO_NESTED;
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

function onChangeRelationshipDirection(nextDirectionRaw: string): void {
    let nextDirection: RelationshipDirection;

    if (nextDirectionRaw === RELATIONSHIP_DIRECTION_NESTED_TO_OUTER) {
        nextDirection = RELATIONSHIP_DIRECTION_NESTED_TO_OUTER;
    } else {
        nextDirection = RELATIONSHIP_DIRECTION_OUTER_TO_NESTED;
    }

    const nextIsInverse =
        nextDirection === RELATIONSHIP_DIRECTION_NESTED_TO_OUTER;

    onUpdateInverse(nextIsInverse);
}

function onUpdateInverse(nextIsInverseRaw: boolean): void {
    const nextIsInverse = Boolean(nextIsInverseRaw);

    let nextPath: [string, string][];

    if (anchorGraphSlug === innerGraphSlug) {
        nextPath = relationship.path;
    } else {
        let nextStartingSlug: string | undefined;

        if (nextIsInverse && innerGraphSlug) {
            nextStartingSlug = innerGraphSlug;
        } else {
            nextStartingSlug = anchorGraphSlug;
        }

        nextPath = [];

        if (nextStartingSlug) {
            nextPath.push([nextStartingSlug, ""]);
        }
    }

    const updatedRelationship: RelationshipState = {
        ...relationship,
        is_inverse: nextIsInverse,
        path: nextPath,
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
                <Tag
                    style="padding: 0.5rem 1rem"
                    icon="pi pi-link"
                    :value="$gettext('Relationship')"
                />

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
                        anchorGraphSlug === innerGraphSlug
                    "
                    :model-value="currentRelationshipDirection"
                    :options="relationshipDirectionOptions"
                    option-label="label"
                    option-value="value"
                    class="relationship-direction-select"
                    :placeholder="$gettext('Direction')"
                    :aria-label="$gettext('Relationship direction')"
                    :title="
                        $gettext(
                            'Choose whether the relationship goes from the outer group to the nested group, or the other way around.',
                        )
                    "
                    @update:model-value="onChangeRelationshipDirection"
                />

                <Select
                    v-if="hasCompatibleRelationshipNodes"
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

.relationship-inline-close {
    margin-inline-start: auto;
}

.relationship-error-message {
    flex: 1 1 auto;
}
</style>
