<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import QueryAddButtons from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryAddButtons.vue";
import QueryGroupHeader from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryGroupHeader.vue";
import QueryReadOnlyItem from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryReadOnlyItem.vue";
import QueryRelatedLink from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryRelatedLink.vue";
import QueryRow from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryRow.vue";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import {
    LogicToken,
    QUERY_BUILDER_ITEM_GROUP,
    QUERY_BUILDER_ITEM_RELATED_GROUP,
    QUERY_BUILDER_ITEM_ROW,
} from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    GraphModel,
    QueryBuilderGroup,
    QueryBuilderItem,
    QueryBuilderRelatedGroup,
} from "@/arches_search/AdvancedSearch/types.ts";

const GROUP_DEPTH_COLOR_COUNT = 3;

const {
    containerId,
    items,
    logic,
    depth,
    emptyMessage = "",
} = defineProps<{
    containerId: string;
    items: QueryBuilderItem[];
    logic: LogicToken;
    depth: number;
    emptyMessage?: string;
}>();

const graphs = inject<Ref<GraphModel[]>>("graphs")!;

const { $gettext, $pgettext } = useGettext();
const queryBuilder = useQueryBuilder();
const { selectedItemIds } = queryBuilder;

const isAllLogic = computed<boolean>(() => logic === LogicToken.AND);

const connectorLabel = computed<string>(() => {
    if (isAllLogic.value) {
        return $gettext("AND");
    }
    return $gettext("OR");
});

const leadText = computed<string>(() => {
    if (depth === 0) {
        return "";
    }
    return $pgettext("Query group: 'where [first condition]'", "where");
});

const emptyHint = computed<string>(() => {
    if (emptyMessage) {
        return emptyMessage;
    }
    if (depth === 0) {
        return $gettext(
            "No conditions yet. Add one below, or click Search to return every record of this model.",
        );
    }
    return $gettext("Empty group. Add conditions with the buttons below.");
});

const groupDepthClass = computed<string>(
    () => `query-group-depth-${depth % GROUP_DEPTH_COLOR_COUNT}`,
);

function isGroupItem(
    item: QueryBuilderItem,
): item is QueryBuilderGroup | QueryBuilderRelatedGroup {
    return (
        item.itemType === QUERY_BUILDER_ITEM_GROUP ||
        item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP
    );
}

function groupClasses(
    item: QueryBuilderGroup | QueryBuilderRelatedGroup,
): Record<string, boolean> {
    const isRelated = item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP;
    return {
        [groupDepthClass.value]: !isRelated,
        "query-group-related": isRelated,
        "query-group-selected": selectedItemIds.value.includes(item.id),
    };
}

function relatedEmptyHint(relatedGroup: QueryBuilderRelatedGroup): string {
    if (!relatedGroup.targetGraphSlug) {
        return $gettext("Choose the related model and how it is linked.");
    }
    const targetGraphName =
        graphs.value.find(
            (graph) => graph.slug === relatedGroup.targetGraphSlug,
        )?.name ?? relatedGroup.targetGraphSlug;
    return $gettext(
        "Any related %{model} record counts. Add conditions to narrow it down.",
        { model: targetGraphName },
    );
}

function groupEmptyMessage(
    item: QueryBuilderGroup | QueryBuilderRelatedGroup,
): string {
    if (item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP) {
        return relatedEmptyHint(item);
    }
    return "";
}

function onToggleLogic(): void {
    queryBuilder.toggleGroupLogic(containerId);
}
</script>

<template>
    <div class="query-item-list">
        <span
            v-if="items.length === 0"
            class="query-item-list-hint"
        >
            <i
                aria-hidden="true"
                class="pi pi-info-circle"
            />
            <span>{{ emptyHint }}</span>
        </span>

        <div
            v-for="(item, itemIndex) in items"
            :key="item.id"
            class="query-item"
        >
            <Button
                v-if="itemIndex > 0"
                class="query-item-connector"
                size="small"
                :class="{ 'query-item-connector-or': !isAllLogic }"
                :label="connectorLabel"
                :title="$gettext('Switch this group between ALL and ANY')"
                @click="onToggleLogic"
            />
            <span
                v-else
                class="query-item-lead"
            >
                {{ leadText }}
            </span>

            <QueryRow
                v-if="item.itemType === QUERY_BUILDER_ITEM_ROW"
                :row-id="item.id"
                :clause="item.clause"
            />
            <div
                v-else-if="isGroupItem(item)"
                class="query-group"
                :class="groupClasses(item)"
            >
                <QueryGroupHeader
                    :group-id="item.id"
                    :label="item.label"
                    :logic="item.logic"
                    :is-related="
                        item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP
                    "
                />
                <div class="query-group-body">
                    <QueryRelatedLink
                        v-if="
                            item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP
                        "
                        :group-id="item.id"
                        :anchor-graph-slug="item.anchorGraphSlug"
                        :target-graph-slug="item.targetGraphSlug"
                        :relationship="item.relationship"
                    />
                    <QueryItemList
                        :container-id="item.id"
                        :items="item.items"
                        :logic="item.logic"
                        :depth="depth + 1"
                        :empty-message="groupEmptyMessage(item)"
                    />
                    <QueryAddButtons
                        :container-id="item.id"
                        :is-nested="true"
                    />
                </div>
            </div>
            <QueryReadOnlyItem
                v-else
                :item-id="item.id"
            />
        </div>
    </div>
</template>

<style scoped>
.query-item-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.query-item-list .query-item-list-hint {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding-block: 0.8rem 0.4rem;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
}

.query-item-list .query-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}

.query-item-list .query-item-lead,
.query-item-list .query-item-connector {
    flex-shrink: 0;
    inline-size: 4.9rem;
    margin-block-start: 1.1rem;
}

.query-item-list .query-item-lead {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 600;
    text-align: end;
}

.query-item-list .query-item-connector {
    padding-block: 0.4rem;
    border: none;
    background: var(--arches-search-logic-and-bg);
    color: var(--arches-search-logic-and-text);
    font-size: 1rem;
    font-weight: 800;
    letter-spacing: 0.06rem;
}

.query-item-list .query-item-connector.query-item-connector-or {
    background: var(--arches-search-logic-or-bg);
    color: var(--arches-search-logic-or-text);
}

.query-item-list .query-group {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
    overflow: hidden;
    border: 0.2rem solid var(--query-group-border);
    border-radius: 1rem;
    background: var(--query-group-bg);
    transition: box-shadow 0.15s;
}

.query-item-list .query-group.query-group-depth-0 {
    --query-group-bg: var(--arches-search-query-group-0-bg);
    --query-group-border: var(--arches-search-query-group-0-border);
    --query-group-header: var(--arches-search-query-group-0-header);
}

.query-item-list .query-group.query-group-depth-1 {
    --query-group-bg: var(--arches-search-query-group-1-bg);
    --query-group-border: var(--arches-search-query-group-1-border);
    --query-group-header: var(--arches-search-query-group-1-header);
}

.query-item-list .query-group.query-group-depth-2 {
    --query-group-bg: var(--arches-search-query-group-2-bg);
    --query-group-border: var(--arches-search-query-group-2-border);
    --query-group-header: var(--arches-search-query-group-2-header);
}

.query-item-list .query-group.query-group-related {
    --query-group-bg: var(--arches-search-query-related-bg);
    --query-group-border: var(--arches-search-query-related-border);
    --query-group-header: var(--arches-search-query-related-header);
}

.query-item-list .query-group.query-group-selected {
    box-shadow: 0 0 0 0.3rem var(--arches-search-primary-muted-bg);
}

.query-item-list .query-group-body {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    padding: 1rem 1.2rem;
}
</style>
