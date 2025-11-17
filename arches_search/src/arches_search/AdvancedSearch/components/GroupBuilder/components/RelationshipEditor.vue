<script setup lang="ts">
import { computed, inject, watch } from "vue";

import { useGettext } from "vue3-gettext";

import SelectButton from "primevue/selectbutton";

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

const { relationship, anchorGraphSlug, innerGraphSlug } = defineProps<{
    relationship: RelationshipState;
    anchorGraphSlug: string;
    innerGraphSlug?: string;
}>();

const traversalQuantifierOptions = computed<{ label: string; value: string }[]>(
    () => {
        return [
            {
                label: $gettext("Any"),
                value: TRAVERSAL_QUANTIFIER_ANY,
            },
            {
                label: $gettext("All"),
                value: TRAVERSAL_QUANTIFIER_ALL,
            },
            {
                label: $gettext("None"),
                value: TRAVERSAL_QUANTIFIER_NONE,
            },
        ];
    },
);

const relationshipDirectionOptions = computed<RelationshipDirectionOption[]>(
    () => {
        return [
            {
                label: $gettext("From outer group to nested group"),
                value: RELATIONSHIP_DIRECTION_OUTER_TO_NESTED,
            },
            {
                label: $gettext("From nested group to outer group"),
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
</script>

<template>
    <div class="relationship">
        <div class="relationship-header-row">
            <span class="relationship-label">
                {{ $gettext("Relationship") }}
            </span>
        </div>

        <div class="relationship-row">
            <label class="relationship-inline-label">
                {{ $gettext("Relationship direction:") }}
            </label>

            <SelectButton
                :model-value="currentRelationshipDirection"
                :options="relationshipDirectionOptions"
                option-label="label"
                option-value="value"
                :allow-empty="false"
                class="relationship-direction-select"
                @update:model-value="onChangeRelationshipDirection"
            />
        </div>

        <div
            v-if="anchorGraph"
            class="relationship-path-row"
        >
            <label class="relationship-inline-label">
                {{ $gettext("Relationship node:") }}
            </label>

            <PathBuilder
                :anchor-graph="anchorGraph"
                :max-path-segments="1"
                :path-sequence="relationship.path"
                @update:path-sequence="onUpdatePathSequence"
            />
        </div>

        <div class="relationship-row">
            <label class="relationship-inline-label">
                {{ $gettext("Quantifier:") }}
            </label>

            <SelectButton
                :model-value="currentTraversalQuantifier"
                :options="traversalQuantifierOptions"
                option-label="label"
                option-value="value"
                :allow-empty="false"
                class="relationship-quantifier-select"
                @update:model-value="onChangeTraversalQuantifier"
            />
        </div>
    </div>
</template>

<style scoped>
.relationship {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
    border-radius: 0.75rem;
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
}

.relationship-header-row {
    display: flex;
    align-items: center;
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.relationship-label {
    color: var(--p-text-color-secondary);
    text-transform: uppercase;
}

.relationship-row,
.relationship-path-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    align-items: center;
}

.relationship-row > label,
.relationship-path-row > label {
    margin-bottom: 0;
}
</style>
