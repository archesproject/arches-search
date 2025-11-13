<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";
import SelectButton from "primevue/selectbutton";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import PathBuilder from "@/arches_search/AdvancedSearch/components/GroupPayloadBuilder/components/PathBuilder.vue";

type RelationshipState = NonNullable<GroupPayload["relationship"]>;
type TraversalQuantifier = RelationshipState["traversal_quantifiers"][number];
type GraphSummary = { slug?: string; [key: string]: unknown };

type RelationshipDirectionOption = {
    label: string;
    value: "OUTER_TO_NESTED" | "NESTED_TO_OUTER";
};

const props = defineProps<{
    relationship: RelationshipState;
    anchorGraphSlug: string;
    innerGraphSlug?: string;
}>();

const emit = defineEmits<{
    (event: "update:relationship", value: RelationshipState): void;
}>();

const { $gettext } = useGettext();

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

if (!graphs) {
    throw new Error("RelationshipEditor is missing graphs injection.");
}

const traversalQuantifierOptions = computed<{ label: string; value: string }[]>(
    function getTraversalQuantifierOptions() {
        return [
            {
                label: $gettext("Any"),
                value: "ANY",
            },
            {
                label: $gettext("All"),
                value: "ALL",
            },
            {
                label: $gettext("None"),
                value: "NONE",
            },
        ];
    },
);

const relationshipDirectionOptions = computed<RelationshipDirectionOption[]>(
    function getRelationshipDirectionOptions() {
        return [
            {
                label: $gettext("From outer group to nested group"),
                value: "OUTER_TO_NESTED",
            },
            {
                label: $gettext("From nested group to outer group"),
                value: "NESTED_TO_OUTER",
            },
        ];
    },
);

const selectedTraversalQuantifier = computed<string>({
    get(): string {
        const firstQuantifierRaw = props.relationship
            .traversal_quantifiers[0] as unknown as string | undefined;

        if (
            firstQuantifierRaw === "ALL" ||
            firstQuantifierRaw === "NONE" ||
            firstQuantifierRaw === "ANY"
        ) {
            return firstQuantifierRaw;
        }

        return "ANY";
    },
    set(nextQuantifierRaw: string): void {
        const normalizedQuantifier = String(nextQuantifierRaw).toUpperCase();

        const safeQuantifierString =
            normalizedQuantifier === "ALL" ||
            normalizedQuantifier === "NONE" ||
            normalizedQuantifier === "ANY"
                ? normalizedQuantifier
                : "ANY";

        const safeQuantifier =
            safeQuantifierString as unknown as TraversalQuantifier;

        const updatedRelationship: RelationshipState = {
            ...props.relationship,
            traversal_quantifiers: [
                safeQuantifier,
            ] as RelationshipState["traversal_quantifiers"],
        };

        emit("update:relationship", updatedRelationship);
    },
});

const selectedRelationshipDirection = computed<string>({
    get(): string {
        return props.relationship.is_inverse
            ? "NESTED_TO_OUTER"
            : "OUTER_TO_NESTED";
    },
    set(nextDirectionRaw: string): void {
        const safeDirection =
            nextDirectionRaw === "NESTED_TO_OUTER"
                ? "NESTED_TO_OUTER"
                : "OUTER_TO_NESTED";

        const nextIsInverse = safeDirection === "NESTED_TO_OUTER";

        onUpdateInverse(nextIsInverse);
    },
});

const startingGraphSlug = computed<string>(function getStartingGraphSlug() {
    if (props.relationship.is_inverse && props.innerGraphSlug) {
        return props.innerGraphSlug;
    }
    return props.anchorGraphSlug;
});

const anchorGraph = computed<GraphSummary | null>(function getAnchorGraph() {
    const graphsArray = graphs.value;

    if (!graphsArray || graphsArray.length === 0) {
        return null;
    }

    const directMatch = graphsArray.find(function matchGraphSummary(
        graphSummary: GraphSummary,
    ) {
        return graphSummary.slug === startingGraphSlug.value;
    });

    if (directMatch) {
        return directMatch;
    }

    return graphsArray[0];
});

function onUpdateInverse(nextIsInverseRaw: boolean): void {
    const nextIsInverse = Boolean(nextIsInverseRaw);

    const nextStartingSlug =
        nextIsInverse && props.innerGraphSlug
            ? props.innerGraphSlug
            : props.anchorGraphSlug;

    const nextPath: [string, string][] = nextStartingSlug
        ? [[nextStartingSlug, ""]]
        : [];

    const updatedRelationship: RelationshipState = {
        ...props.relationship,
        is_inverse: nextIsInverse,
        path: nextPath,
    };

    emit("update:relationship", updatedRelationship);
}

function onUpdatePathSequence(nextPathSequence: [string, string][]): void {
    const updatedRelationship: RelationshipState = {
        ...props.relationship,
        path: nextPathSequence,
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
                {{ $gettext("Relationship direction") }}
            </label>

            <SelectButton
                v-model="selectedRelationshipDirection"
                :options="relationshipDirectionOptions"
                option-label="label"
                option-value="value"
                :allow-empty="false"
                class="relationship-direction-select"
            />
        </div>

        <div
            v-if="anchorGraph"
            class="relationship-path-row"
        >
            <label class="relationship-inline-label">
                {{ $gettext("Relationship node") }}
            </label>

            <PathBuilder
                :anchor-graph="anchorGraph as GraphSummary"
                :max-path-segments="1"
                :path-sequence="
                    props.relationship.path as readonly (readonly [
                        string,
                        string,
                    ])[]
                "
                @update:path-sequence="onUpdatePathSequence"
            />
        </div>

        <div class="relationship-row">
            <label class="relationship-inline-label">
                {{ $gettext("Quantifier") }}
            </label>

            <SelectButton
                v-model="selectedTraversalQuantifier"
                :options="traversalQuantifierOptions"
                option-label="label"
                option-value="value"
                :allow-empty="false"
                class="relationship-quantifier-select"
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
    border: 0.0625rem solid var(--p-content-border-color);
    background: var(--p-content-background);
}

.relationship-header-row {
    display: flex;
    align-items: center;
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 0.0625rem solid var(--p-content-border-color);
}

.relationship-label {
    font-weight: 600;
    color: var(--p-text-color-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.relationship-row,
.relationship-path-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.relationship-inline-label {
    flex: 0 0 11rem;
    font-weight: 500;
    color: var(--p-text-color);
}

.relationship-row > :not(.relationship-inline-label),
.relationship-path-row > :not(.relationship-inline-label) {
    flex: 1 1 12rem;
}

.relationship-direction-select {
    min-width: 14rem;
}

.relationship-quantifier-select {
    min-width: 10rem;
}
</style>
