import { computed, inject, provide, ref, watch } from "vue";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import {
    addGroup,
    addRelatedGroup,
    addRow,
    buildPrunedPayload,
    canGroupQueryBuilderItems,
    createQueryBuilderRoot,
    draftDiffersFromApplied,
    findQueryBuilderItem,
    groupQueryBuilderItems,
    queryBuilderRootFromPayload,
    removeQueryBuilderItem,
    setGroupLabel,
    setRelatedRelationship,
    setRelatedTarget,
    setRowClause,
    toggleGroupLogic,
    toggleRelatedNot,
    toggleRowNot,
} from "@/arches_search/AdvancedSearch/utils/query-builder.ts";
import { QUERY_BUILDER_ITEM_RELATED_GROUP } from "@/arches_search/AdvancedSearch/types.ts";

import type { ComputedRef, InjectionKey, Ref } from "vue";
import type {
    AdvancedSearchFacet,
    AdvancedSearchOperandComponent,
    GraphModel,
    GroupPayload,
    LiteralClause,
    Node,
    QueryBuilderGroup,
    QueryBuilderItem,
    QueryBuilderLookups,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

interface QueryBuilderContext {
    root: ComputedRef<QueryBuilderGroup | null>;
    lookups: QueryBuilderLookups;
    prunedPayload: ComputedRef<GroupPayload | null>;
    hasUnsearchedChanges: ComputedRef<boolean>;
    isSelecting: ComputedRef<boolean>;
    selectedItemIds: ComputedRef<string[]>;
    canGroupSelection: ComputedRef<boolean>;
    startQuery(graphSlug: string): void;
    clearQuery(): void;
    addRow(containerId: string): string | null;
    addGroup(containerId: string): string | null;
    addRelatedGroup(containerId: string): string | null;
    removeItem(itemId: string): void;
    toggleGroupLogic(containerId: string): void;
    setGroupLabel(containerId: string, label: string): void;
    setRowClause(rowId: string, clause: LiteralClause): void;
    toggleRowNot(rowId: string): void;
    setRelatedTarget(groupId: string, targetGraphSlug: string): void;
    setRelatedRelationship(
        groupId: string,
        relationship: RelationshipBlock,
    ): void;
    toggleRelatedNot(groupId: string): void;
    startSelecting(): void;
    stopSelecting(): void;
    toggleItemSelected(itemId: string): void;
    groupSelectedItems(): void;
}

const QUERY_BUILDER_KEY: InjectionKey<QueryBuilderContext> =
    Symbol("queryBuilder");

function createQueryBuilder({
    graphs,
    datatypesToAdvancedSearchFacets,
    operandComponents,
    getNodesForGraphId,
}: {
    graphs: Ref<GraphModel[]>;
    datatypesToAdvancedSearchFacets: Ref<Record<string, AdvancedSearchFacet[]>>;
    operandComponents: Ref<AdvancedSearchOperandComponent[]>;
    getNodesForGraphId: (graphId: string) => Promise<Node[]>;
}): QueryBuilderContext {
    const { advancedQuery, advancedQueryDraft, setAdvancedQueryDraft } =
        useSearchFilters();

    const nodeDatatypesByGraphSlug = ref<
        Record<string, Record<string, string>>
    >({});
    const requestedGraphSlugs = new Set<string>();
    const isSelectingItems = ref(false);
    const selectedItemIdList = ref<string[]>([]);

    const lookups: QueryBuilderLookups = {
        getNodeDatatype: (graphSlug, nodeAlias) =>
            nodeDatatypesByGraphSlug.value[graphSlug]?.[nodeAlias],
        getOperatorArity: (datatype, operator) =>
            datatypesToAdvancedSearchFacets.value[datatype]?.find(
                (facet) => facet.operator === operator,
            )?.arity,
        getOperandComponent: (datatype) =>
            operandComponents.value.find(
                (operandComponent) => operandComponent.datatype_id === datatype,
            ),
    };

    const root = computed<QueryBuilderGroup | null>(
        () => advancedQueryDraft.value,
    );

    const prunedPayload = computed<GroupPayload | null>(() => {
        if (!root.value) {
            return null;
        }
        return buildPrunedPayload(root.value, lookups);
    });

    const hasUnsearchedChanges = computed<boolean>(() =>
        draftDiffersFromApplied(root.value, advancedQuery.value, lookups),
    );

    const isSelecting = computed<boolean>(() => isSelectingItems.value);

    const selectedItemIds = computed<string[]>(() => selectedItemIdList.value);

    const canGroupSelection = computed<boolean>(() => {
        if (!root.value) {
            return false;
        }
        return canGroupQueryBuilderItems(root.value, selectedItemIdList.value);
    });

    watch(
        advancedQuery,
        (appliedQuery) => {
            if (!advancedQueryDraft.value && appliedQuery) {
                setAdvancedQueryDraft(
                    queryBuilderRootFromPayload(appliedQuery),
                );
            }
        },
        { immediate: true },
    );

    watch(
        [root, graphs],
        ([currentRoot]) => {
            if (!currentRoot) {
                return;
            }
            for (const graphSlug of graphSlugsIn(currentRoot)) {
                void loadNodeDatatypes(graphSlug);
            }
        },
        { immediate: true },
    );

    async function loadNodeDatatypes(graphSlug: string): Promise<void> {
        const graph = graphs.value.find(
            (candidate) => candidate.slug === graphSlug,
        );
        if (!graph || requestedGraphSlugs.has(graphSlug)) {
            return;
        }
        requestedGraphSlugs.add(graphSlug);

        try {
            const nodes = await getNodesForGraphId(graph.graphid);
            nodeDatatypesByGraphSlug.value = {
                ...nodeDatatypesByGraphSlug.value,
                [graphSlug]: Object.fromEntries(
                    nodes.map((node) => [node.alias, node.datatype]),
                ),
            };
        } catch (error) {
            requestedGraphSlugs.delete(graphSlug);
            console.error(error);
        }
    }

    function updateRoot(
        transform: (currentRoot: QueryBuilderGroup) => QueryBuilderGroup,
    ): void {
        if (root.value) {
            setAdvancedQueryDraft(transform(root.value));
        }
    }

    function startQuery(graphSlug: string): void {
        stopSelecting();
        setAdvancedQueryDraft(createQueryBuilderRoot(graphSlug));
    }

    function clearQuery(): void {
        stopSelecting();
        setAdvancedQueryDraft(null);
    }

    function addRowToContainer(containerId: string): string | null {
        if (!root.value) {
            return null;
        }
        const result = addRow(root.value, containerId);
        setAdvancedQueryDraft(result.root);
        return result.rowId;
    }

    function addGroupToContainer(containerId: string): string | null {
        if (!root.value) {
            return null;
        }
        const result = addGroup(root.value, containerId);
        setAdvancedQueryDraft(result.root);
        return result.groupId;
    }

    function addRelatedGroupToContainer(containerId: string): string | null {
        if (!root.value) {
            return null;
        }
        const result = addRelatedGroup(root.value, containerId);
        setAdvancedQueryDraft(result.root);
        return result.groupId;
    }

    function startSelecting(): void {
        isSelectingItems.value = true;
    }

    function stopSelecting(): void {
        isSelectingItems.value = false;
        selectedItemIdList.value = [];
    }

    function toggleItemSelected(itemId: string): void {
        if (selectedItemIdList.value.includes(itemId)) {
            selectedItemIdList.value = selectedItemIdList.value.filter(
                (selectedItemId) => selectedItemId !== itemId,
            );
            return;
        }
        selectedItemIdList.value = [...selectedItemIdList.value, itemId];
    }

    function groupSelectedItems(): void {
        if (!root.value) {
            return;
        }
        const result = groupQueryBuilderItems(
            root.value,
            selectedItemIdList.value,
        );
        if (!result) {
            return;
        }
        setAdvancedQueryDraft(result.root);
        stopSelecting();
    }

    function removeItem(itemId: string): void {
        if (!root.value) {
            return;
        }
        const nextRoot = removeQueryBuilderItem(root.value, itemId);
        setAdvancedQueryDraft(nextRoot);
        selectedItemIdList.value = selectedItemIdList.value.filter(
            (selectedItemId) =>
                findQueryBuilderItem(nextRoot, selectedItemId) !== null,
        );
    }

    function toggleContainerLogic(containerId: string): void {
        updateRoot((currentRoot) => toggleGroupLogic(currentRoot, containerId));
    }

    function setContainerLabel(containerId: string, label: string): void {
        updateRoot((currentRoot) =>
            setGroupLabel(currentRoot, containerId, label),
        );
    }

    function setClauseOfRow(rowId: string, clause: LiteralClause): void {
        updateRoot((currentRoot) => setRowClause(currentRoot, rowId, clause));
    }

    function toggleNotOfRow(rowId: string): void {
        updateRoot((currentRoot) => toggleRowNot(currentRoot, rowId));
    }

    function setTargetOfRelatedGroup(
        groupId: string,
        targetGraphSlug: string,
    ): void {
        updateRoot((currentRoot) =>
            setRelatedTarget(currentRoot, groupId, targetGraphSlug),
        );
    }

    function setRelationshipOfRelatedGroup(
        groupId: string,
        relationship: RelationshipBlock,
    ): void {
        updateRoot((currentRoot) =>
            setRelatedRelationship(currentRoot, groupId, relationship),
        );
    }

    function toggleNotOfRelatedGroup(groupId: string): void {
        updateRoot((currentRoot) => toggleRelatedNot(currentRoot, groupId));
    }

    return {
        root,
        lookups,
        prunedPayload,
        hasUnsearchedChanges,
        isSelecting,
        selectedItemIds,
        canGroupSelection,
        startQuery,
        clearQuery,
        addRow: addRowToContainer,
        addGroup: addGroupToContainer,
        addRelatedGroup: addRelatedGroupToContainer,
        removeItem,
        toggleGroupLogic: toggleContainerLogic,
        setGroupLabel: setContainerLabel,
        setRowClause: setClauseOfRow,
        toggleRowNot: toggleNotOfRow,
        setRelatedTarget: setTargetOfRelatedGroup,
        setRelatedRelationship: setRelationshipOfRelatedGroup,
        toggleRelatedNot: toggleNotOfRelatedGroup,
        startSelecting,
        stopSelecting,
        toggleItemSelected,
        groupSelectedItems,
    };
}

function graphSlugsIn(root: QueryBuilderGroup): Set<string> {
    const graphSlugs = new Set<string>([root.graphSlug]);

    function visit(items: QueryBuilderItem[]): void {
        for (const item of items) {
            if (item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP) {
                if (item.targetGraphSlug) {
                    graphSlugs.add(item.targetGraphSlug);
                }
                visit(item.items);
            } else if ("items" in item) {
                visit(item.items);
            }
        }
    }

    visit(root.items);
    return graphSlugs;
}

export function provideQueryBuilder(
    sources: Parameters<typeof createQueryBuilder>[0],
): QueryBuilderContext {
    const queryBuilder = createQueryBuilder(sources);
    provide(QUERY_BUILDER_KEY, queryBuilder);
    return queryBuilder;
}

export function useQueryBuilder(): QueryBuilderContext {
    const queryBuilder = inject(QUERY_BUILDER_KEY);

    if (!queryBuilder) {
        throw new Error(
            "a parent component must call provideQueryBuilder before using useQueryBuilder in a child component",
        );
    }

    return queryBuilder;
}
