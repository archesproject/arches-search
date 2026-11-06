<script setup lang="ts">
import { computed } from "vue";

import QueryRowTags from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryRowTags.vue";
import RelationshipEditor from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/RelationshipEditor.vue";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";

import {
    QUANTIFIER_ALL,
    QUANTIFIER_NONE,
} from "@/arches_search/AdvancedSearch/types.ts";

import type { RelationshipBlock } from "@/arches_search/AdvancedSearch/types.ts";

const RELATED_BADGE_KIND = "related";
const RELATED_BADGE_ICON = "pi pi-sitemap";

const { groupId, anchorGraphSlug, targetGraphSlug, relationship } =
    defineProps<{
        groupId: string;
        anchorGraphSlug: string;
        targetGraphSlug: string;
        relationship: RelationshipBlock;
    }>();

const queryBuilder = useQueryBuilder();

const isNegated = computed<boolean>(
    () => relationship.traversal_quantifier === QUANTIFIER_NONE,
);

const canNegate = computed<boolean>(
    () => relationship.traversal_quantifier !== QUANTIFIER_ALL,
);

function onToggleNot(): void {
    queryBuilder.toggleRelatedNot(groupId);
}

function onUpdateRelationship(nextRelationship: RelationshipBlock): void {
    queryBuilder.setRelatedRelationship(groupId, nextRelationship);
}

function onUpdateTarget(nextTargetGraphSlug: string): void {
    queryBuilder.setRelatedTarget(groupId, nextTargetGraphSlug);
}
</script>

<template>
    <div class="query-related-link">
        <QueryRowTags
            :graph-slug="anchorGraphSlug"
            :badge-label="
                $pgettext(
                    'Query condition: \'Related to a [model] via [field]\'',
                    'Related to a',
                )
            "
            :badge-icon="RELATED_BADGE_ICON"
            :badge-kind="RELATED_BADGE_KIND"
            :is-negated="isNegated"
            :can-negate="canNegate"
            @toggle-not="onToggleNot"
        />
        <RelationshipEditor
            :relationship="relationship"
            :anchor-graph-slug="anchorGraphSlug"
            :inner-graph-slug="targetGraphSlug"
            @update:relationship="onUpdateRelationship"
            @update:inner-graph-slug="onUpdateTarget"
        />
    </div>
</template>

<style scoped>
.query-related-link {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
    padding: 0.9rem 1.2rem;
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.8rem;
    background: var(--p-content-background);
}
</style>
