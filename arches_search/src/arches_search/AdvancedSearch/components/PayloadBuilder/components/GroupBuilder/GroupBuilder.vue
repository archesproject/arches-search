<script setup lang="ts">
import { ref, computed, watchEffect, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Card from "primevue/card";
import Drawer from "primevue/drawer";

import GroupBracket from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/GroupBracket.vue";
import GroupHeader from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/GroupHeader.vue";
import GroupFooter from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/GroupFooter.vue";
import RelationshipEditor from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/RelationshipEditor.vue";
import ClauseBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/ClauseBuilder/ClauseBuilder.vue";

import {
    makeEmptyGroupPayload,
    toggleLogic,
    addChildGroupLikeParent,
    addEmptyLiteralClauseToGroup,
    addEmptySearchModelsClauseToGroup,
    removeClauseAtIndex,
    addRelationshipIfMissing,
    setGraphSlugAndResetIfChanged,
    removeChildGroupAtIndexAndReconcile,
    setClauseAtIndex,
    replaceChildGroupAtIndexAndReconcile,
    setRelationshipAndReconcileClauses,
} from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";

import type {
    GraphModel,
    GroupPayload,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

defineOptions({ name: "GroupBuilder" });

const ITEM_TYPE_CLAUSE = "clause" as const;
const ITEM_TYPE_GROUP = "group" as const;
type ItemType = typeof ITEM_TYPE_CLAUSE | typeof ITEM_TYPE_GROUP;

const { $gettext } = useGettext();
const graphs = inject<Readonly<{ value: GraphModel[] }>>("graphs");

const emit = defineEmits<{ "update:modelValue": [GroupPayload]; remove: [] }>();

const { modelValue, isRoot, relationshipToParent } = defineProps<{
    modelValue?: GroupPayload;
    isRoot?: boolean;
    relationshipToParent?: GroupPayload["relationship"];
}>();

const showMapDrawer = ref(false);

const group = computed(() => {
    return modelValue ?? makeEmptyGroupPayload();
});

const items = ref<{ id: string; type: ItemType }[]>([]);

const hasRelationship = computed(() => {
    return group.value.relationship !== null;
});

const contentGroup = computed(() => {
    if (hasRelationship.value) {
        return group.value.groups[0] ?? group.value;
    }
    return group.value;
});

const anchor = computed(() => {
    return (
        graphs?.value.find((graphModel) => {
            return graphModel.slug === group.value.graph_slug;
        }) ?? null
    );
});

const contentAnchorGraph = computed(() => {
    return (
        graphs?.value.find((graphModel) => {
            return graphModel.slug === contentGroup.value.graph_slug;
        }) ?? null
    );
});

const shouldShowBracket = computed(() => {
    return items.value.length >= 2;
});

const hasContent = computed(() => {
    return items.value.length > 0;
});

const rootStyle = computed(() => {
    if (isRoot) {
        return { borderRadius: 0, borderBottom: "none" };
    }
    return undefined;
});

watchEffect(() => {
    const currentContentGroup = contentGroup.value;
    const clauseCount = items.value.filter((item) => {
        return item.type === ITEM_TYPE_CLAUSE;
    }).length;
    const groupCount = items.value.filter((item) => {
        return item.type === ITEM_TYPE_GROUP;
    }).length;
    if (
        clauseCount === currentContentGroup.clauses.length &&
        groupCount === currentContentGroup.groups.length
    ) {
        return;
    }
    items.value = [
        ...currentContentGroup.clauses.map(() => {
            return { id: crypto.randomUUID(), type: ITEM_TYPE_CLAUSE };
        }),
        ...currentContentGroup.groups.map(() => {
            return { id: crypto.randomUUID(), type: ITEM_TYPE_GROUP };
        }),
    ];
});

function findItemIndex(itemId: string, itemType: ItemType) {
    let count = 0;
    for (const item of items.value) {
        if (item.id === itemId) {
            return count;
        }
        if (item.type === itemType) {
            count++;
        }
    }
    return -1;
}

function emitUpdate(updatedContentGroup: GroupPayload) {
    if (hasRelationship.value) {
        emit("update:modelValue", {
            ...group.value,
            groups: [updatedContentGroup, ...group.value.groups.slice(1)],
        });
    } else {
        emit("update:modelValue", updatedContentGroup);
    }
}

function ensureHasInnerGroup(container: GroupPayload) {
    if (container.groups.length > 0) {
        return container;
    }
    const withInnerGroup = addChildGroupLikeParent(container);
    return {
        ...withInnerGroup,
        groups: [{ ...withInnerGroup.groups[0], graph_slug: "" }],
    };
}

function addChildGroup(transform: (child: GroupPayload) => GroupPayload) {
    const withNewChild = addChildGroupLikeParent(contentGroup.value);
    const childGroups = withNewChild.groups.slice();
    const lastIndex = childGroups.length - 1;
    childGroups[lastIndex] = transform(childGroups[lastIndex]);
    items.value.push({ id: crypto.randomUUID(), type: ITEM_TYPE_GROUP });
    emitUpdate({ ...withNewChild, groups: childGroups });
}

function onChangeGraph(slug: string) {
    emit("update:modelValue", setGraphSlugAndResetIfChanged(group.value, slug));
}

function onToggleLogic() {
    emitUpdate(toggleLogic(contentGroup.value));
}

function onAddClause() {
    items.value.push({ id: crypto.randomUUID(), type: ITEM_TYPE_CLAUSE });
    emitUpdate(addEmptyLiteralClauseToGroup(contentGroup.value));
}

function onAddStringSearch() {
    items.value.push({ id: crypto.randomUUID(), type: ITEM_TYPE_CLAUSE });
    emitUpdate(addEmptySearchModelsClauseToGroup(contentGroup.value));
}

function onUpdateClause(itemId: string, clause: LiteralClause) {
    const clauseIndex = findItemIndex(itemId, ITEM_TYPE_CLAUSE);
    if (clauseIndex === -1) {
        return;
    }
    emitUpdate(setClauseAtIndex(contentGroup.value, clauseIndex, clause));
}

function onRemoveClause(itemId: string) {
    const clauseIndex = findItemIndex(itemId, ITEM_TYPE_CLAUSE);
    if (clauseIndex === -1) {
        return;
    }
    items.value.splice(
        items.value.findIndex((item) => {
            return item.id === itemId;
        }),
        1,
    );
    emitUpdate(removeClauseAtIndex(contentGroup.value, clauseIndex));
}

function onAddGroup() {
    const inheritedSlug =
        contentGroup.value.groups[0]?.graph_slug ||
        contentGroup.value.graph_slug;
    addChildGroup((child) => {
        return { ...child, graph_slug: inheritedSlug };
    });
}

function onUpdateGroup(itemId: string, updated: GroupPayload) {
    const groupIndex = findItemIndex(itemId, ITEM_TYPE_GROUP);
    if (groupIndex === -1) {
        return;
    }
    emitUpdate(
        replaceChildGroupAtIndexAndReconcile(
            contentGroup.value,
            groupIndex,
            updated,
        ),
    );
}

function onRemoveGroup(itemId: string) {
    const groupIndex = findItemIndex(itemId, ITEM_TYPE_GROUP);
    if (groupIndex === -1) {
        return;
    }
    items.value.splice(
        items.value.findIndex((item) => {
            return item.id === itemId;
        }),
        1,
    );
    emitUpdate(
        removeChildGroupAtIndexAndReconcile(contentGroup.value, groupIndex),
    );
}

function onAddRelationship() {
    const graphSlug = contentGroup.value.graph_slug;
    addChildGroup((child) => {
        const withSlug = { ...child, graph_slug: graphSlug };
        return ensureHasInnerGroup(addRelationshipIfMissing(withSlug));
    });
}

function onUpdateRelationship(relationship: GroupPayload["relationship"]) {
    if (!relationship) {
        emit("remove");
        return;
    }
    emit(
        "update:modelValue",
        ensureHasInnerGroup(
            setRelationshipAndReconcileClauses(group.value, relationship),
        ),
    );
}

function onUpdateInnerGraphSlug(slug: string) {
    const existingInnerGroup = group.value.groups[0];
    if (!existingInnerGroup || existingInnerGroup.graph_slug === slug) {
        return;
    }
    const resetInnerGroup = {
        ...makeEmptyGroupPayload(),
        graph_slug: slug,
        logic: existingInnerGroup.logic,
    };
    let relationship = group.value.relationship;
    if (relationship) {
        relationship = {
            ...relationship,
            path: {
                type: relationship.path.type,
                graph_slug: "",
                node_alias: "",
            },
        };
    }
    emit(
        "update:modelValue",
        setRelationshipAndReconcileClauses(
            { ...group.value, groups: [resetInnerGroup] },
            relationship,
        ),
    );
}
</script>

<template>
    <Card
        class="group-card"
        :style="rootStyle"
    >
        <template
            v-if="isRoot || relationshipToParent != null || hasRelationship"
            #title
        >
            <GroupHeader
                v-if="isRoot || relationshipToParent != null"
                :group-payload="isRoot ? group : contentGroup"
                :is-root="isRoot"
                :relationship-to-parent="relationshipToParent ?? null"
                @change-graph="onChangeGraph"
                @remove-group="emit('remove')"
            />
            <RelationshipEditor
                v-if="hasRelationship"
                class="relationship-editor-inline"
                :style="{ marginBottom: !hasContent ? '1.5rem' : 0 }"
                :anchor-graph-slug="group.graph_slug"
                :inner-graph-slug="group.groups[0]?.graph_slug ?? ''"
                :relationship="group.relationship!"
                @update:relationship="onUpdateRelationship"
                @update:inner-graph-slug="onUpdateInnerGraphSlug"
            />
        </template>

        <template #content>
            <div class="group-content">
                <div
                    v-if="isRoot && !hasContent && !anchor"
                    class="group-helper-note"
                >
                    <div>
                        {{
                            $gettext(
                                "Add a filter to search the database. Groups let you bundle filters",
                            )
                        }}
                    </div>
                    <div>
                        {{
                            $gettext(
                                "Click the group type to change the type of grouping.",
                            )
                        }}
                    </div>
                </div>

                <div
                    v-if="hasContent"
                    :class="[
                        'group-grid',
                        shouldShowBracket && 'group-grid-with-bracket',
                    ]"
                >
                    <GroupBracket
                        :show="shouldShowBracket"
                        :logic="contentGroup.logic"
                        @update:logic="onToggleLogic"
                    />

                    <div class="group-body">
                        <template
                            v-for="item in items"
                            :key="item.id"
                        >
                            <Card
                                v-if="item.type === ITEM_TYPE_CLAUSE"
                                class="clause-card"
                            >
                                <template #content>
                                    <ClauseBuilder
                                        :model-value="
                                            contentGroup.clauses[
                                                findItemIndex(
                                                    item.id,
                                                    ITEM_TYPE_CLAUSE,
                                                )
                                            ]
                                        "
                                        :anchor-graph="contentAnchorGraph!"
                                        @update:model-value="
                                            onUpdateClause(
                                                item.id,
                                                $event as LiteralClause,
                                            )
                                        "
                                        @request:remove="
                                            onRemoveClause(item.id)
                                        "
                                    />
                                </template>
                            </Card>

                            <GroupBuilder
                                v-else-if="item.type === ITEM_TYPE_GROUP"
                                :model-value="
                                    contentGroup.groups[
                                        findItemIndex(item.id, ITEM_TYPE_GROUP)
                                    ]
                                "
                                :relationship-to-parent="
                                    contentGroup.groups[
                                        findItemIndex(item.id, ITEM_TYPE_GROUP)
                                    ]?.relationship ?? null
                                "
                                @update:model-value="
                                    onUpdateGroup(item.id, $event)
                                "
                                @remove="onRemoveGroup(item.id)"
                            />
                        </template>
                    </div>
                </div>
            </div>
        </template>

        <template #footer>
            <GroupFooter
                :disabled="!contentAnchorGraph"
                :is-root="isRoot"
                @add-group="onAddGroup"
                @add-filter="onAddClause"
                @add-string-search="onAddStringSearch"
                @add-relationship="onAddRelationship"
                @add-map-filter="showMapDrawer = true"
                @remove-group="emit('remove')"
            />
        </template>
    </Card>

    <Drawer
        v-model:visible="showMapDrawer"
        :header="$gettext('Map filter')"
        position="right"
        :style="{ width: '32rem', maxWidth: '100vw' }"
    >
        <div class="map-filter-drawer-content">
            {{ $gettext("Map is TBD.") }}
        </div>
    </Drawer>
</template>

<style scoped>
.group-card {
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
    margin-inline-end: 0;
}

.group-card :deep(.p-card-body) {
    gap: 0;
    padding: 1rem;
}

.clause-card {
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
}

.group-content {
    display: flex;
    flex-direction: column;
}

.group-grid {
    display: flex;
    align-items: stretch;
    width: 100%;
    margin-top: 1rem;
    margin-bottom: 1.75rem;
}

.group-grid-with-bracket {
    display: flex;
    align-items: stretch;
    padding-inline-start: 1.5rem;
}

.group-grid-with-bracket :deep(.bracket) {
    flex: 0 0 4rem;
}

.group-body {
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-width: 0;
    margin-inline-end: 5.5rem;
}

.relationship-editor-inline {
    align-self: stretch;
}

.group-helper-note {
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
    margin-bottom: 2rem;
    margin-inline-start: 1.5rem;
}

.map-filter-drawer-content {
    font-size: 1.1rem;
    color: var(--p-text-muted-color);
    padding: 0.5rem 0;
}
</style>
