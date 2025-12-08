<script setup lang="ts">
import { computed, inject, watch } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Card from "primevue/card";

import PathBuilder from "@/arches_search/AdvancedSearch/components/GroupBuilder/components/PathBuilder.vue";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

type RelationshipState = NonNullable<GroupPayload["relationship"]>;
type TraversalQuantifier = RelationshipState["traversal_quantifiers"][number];

type GraphSummary = {
    graphid: string;
    name: string;
    slug: string;
    [key: string]: unknown;
};

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

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

if (!graphs) {
    throw new Error("RelationshipEditor is missing graphs injection.");
}

const emit = defineEmits<{
    (event: "update:relationship", value: RelationshipState | null): void;
}>();

const { relationship, anchorGraphSlug, innerGraphSlug, isRoot } = defineProps<{
    relationship: RelationshipState;
    anchorGraphSlug: string;
    innerGraphSlug?: string;
    isRoot?: boolean;
}>();

const traversalQuantifierOptions = computed<{ label: string; value: string }[]>(
    () => {
        return [
            {
                label: $gettext("Any related record"),
                value: TRAVERSAL_QUANTIFIER_ANY,
            },
            {
                label: $gettext("All related records"),
                value: TRAVERSAL_QUANTIFIER_ALL,
            },
            {
                label: $gettext("No related records"),
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

const startingGraphSlug = computed<string | undefined>(() => {
    if (relationship.is_inverse && innerGraphSlug) {
        return innerGraphSlug;
    }
    return anchorGraphSlug;
});

const anchorGraph = computed<GraphSummary | null>(() => {
    const graphsArray = graphs.value;

    if (!graphsArray || graphsArray.length === 0) {
        return null;
    }

    const directMatch = graphsArray.find((graphSummary) => {
        return graphSummary.slug === startingGraphSlug.value;
    });

    if (directMatch) {
        return directMatch;
    }

    return graphsArray[0];
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

    let nextStartingSlug: string | undefined;

    if (nextIsInverse && innerGraphSlug) {
        nextStartingSlug = innerGraphSlug;
    } else {
        nextStartingSlug = anchorGraphSlug;
    }

    const nextPath: [string, string][] = [];

    if (nextStartingSlug) {
        nextPath.push([nextStartingSlug, ""]);
    }

    const updatedRelationship: RelationshipState = {
        ...relationship,
        is_inverse: nextIsInverse,
        path: nextPath,
    };

    emit("update:relationship", updatedRelationship);
}

function onUpdatePathSequence(
    nextPathSequence: RelationshipPathSequence,
): void {
    const nextPath = nextPathSequence.map((segment) => {
        return [segment[0], segment[1]] as [string, string];
    });

    const updatedRelationship: RelationshipState = {
        ...relationship,
        path: nextPath,
    };

    emit("update:relationship", updatedRelationship);
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

                <Select
                    :model-value="currentRelationshipDirection"
                    :options="relationshipDirectionOptions"
                    option-label="label"
                    option-value="value"
                    class="relationship-direction-select"
                    :placeholder="$gettext('Direction between groups')"
                    :aria-label="$gettext('Relationship direction')"
                    :title="
                        $gettext(
                            'Choose whether the relationship goes from the outer group to the nested group, or the other way around.',
                        )
                    "
                    @update:model-value="onChangeRelationshipDirection"
                />

                <PathBuilder
                    v-if="anchorGraph"
                    :anchor-graph="anchorGraph"
                    :max-path-segments="1"
                    :path-sequence="relationship.path"
                    @update:path-sequence="onUpdatePathSequence"
                />

                <Select
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
</style>
