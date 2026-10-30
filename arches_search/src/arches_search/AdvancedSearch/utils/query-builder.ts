import { isEqual } from "es-toolkit";

import {
    ClauseSubjectTypeToken,
    GraphScopeToken,
    LogicToken,
    QUERY_BUILDER_ITEM_GROUP,
    QUERY_BUILDER_ITEM_LOCKED_CLAUSE,
    QUERY_BUILDER_ITEM_LOCKED_GROUP,
    QUERY_BUILDER_ITEM_RELATED_GROUP,
    QUERY_BUILDER_ITEM_ROW,
} from "@/arches_search/AdvancedSearch/types.ts";

import type {
    GroupPayload,
    LiteralClause,
    LiteralOperand,
    QueryBuilderGroup,
    QueryBuilderItem,
    QueryBuilderLookups,
    QueryBuilderRelatedGroup,
    QueryBuilderRow,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

type QueryBuilderContainer = QueryBuilderGroup | QueryBuilderRelatedGroup;

const CLAUSE_TYPE_LITERAL = "LITERAL";
const QUANTIFIER_ANY = "ANY";
const QUANTIFIER_NONE = "NONE";
const MINIMUM_ITEMS_TO_GROUP = 2;
const SEARCH_MODEL_GEOMETRY = "GeometrySearch";
const SEARCH_MODEL_TERM = "TermSearch";
const SEARCH_MODELS_DATE = ["DateSearch", "DateRangeSearch"];
const DATATYPE_DATE = "date";
const DATATYPE_GEOJSON = "geojson-feature-collection";
const DATATYPE_STRING = "string";

export function createQueryBuilderRoot(graphSlug: string): QueryBuilderGroup {
    return {
        id: crypto.randomUUID(),
        itemType: QUERY_BUILDER_ITEM_GROUP,
        graphSlug,
        logic: LogicToken.AND,
        label: "",
        items: [],
    };
}

export function queryBuilderRootFromPayload(
    payload: GroupPayload,
): QueryBuilderGroup {
    if (isEditablePlainGroup(payload, payload.graph_slug)) {
        return plainGroupFromPayload(payload);
    }
    return {
        ...createQueryBuilderRoot(payload.graph_slug),
        items: [lockedGroup(payload)],
    };
}

export function queryBuilderRootToPayload(
    root: QueryBuilderGroup,
): GroupPayload {
    return plainGroupToPayload(root);
}

// The query that is sent: rows still being filled in and groups left empty
// are dropped, and a root with nothing left becomes no query at all.
export function buildPrunedPayload(
    root: QueryBuilderGroup,
    lookups: QueryBuilderLookups,
): GroupPayload | null {
    const prunedItems = pruneItems(root.items, lookups);
    if (prunedItems.length === 0) {
        return null;
    }
    return plainGroupToPayload({ ...root, items: prunedItems });
}

export function draftDiffersFromApplied(
    draft: QueryBuilderGroup | null,
    applied: GroupPayload | null,
    lookups: QueryBuilderLookups,
): boolean {
    let draftPayload: GroupPayload | null = null;
    if (draft) {
        draftPayload = buildPrunedPayload(draft, lookups);
    }
    return !isEqual(draftPayload, applied);
}

// A clause on any date or any geometry has no node, so its datatype comes from
// the search models it reads.
export function getClauseDatatype(
    clause: LiteralClause,
    lookups: QueryBuilderLookups,
): string | undefined {
    if (clause.subject.type === ClauseSubjectTypeToken.SEARCH_MODELS) {
        return searchModelsDatatype(clause.subject.search_models);
    }
    if (!clause.subject.node_alias) {
        return undefined;
    }
    return lookups.getNodeDatatype(
        clause.subject.graph_slug,
        clause.subject.node_alias,
    );
}

export function isClauseComplete(
    clause: LiteralClause,
    lookups: QueryBuilderLookups,
): boolean {
    if (!clause.operator) {
        return false;
    }
    if (
        clause.subject.type === ClauseSubjectTypeToken.NODE &&
        !clause.subject.node_alias
    ) {
        return false;
    }

    const datatype = getClauseDatatype(clause, lookups);

    let requiredOperandCount = clause.operands.length;
    if (datatype) {
        requiredOperandCount =
            lookups.getOperatorArity(datatype, clause.operator) ??
            clause.operands.length;
    }

    if (clause.operands.length < requiredOperandCount) {
        return false;
    }
    return clause.operands
        .slice(0, requiredOperandCount)
        .every((operand) => !isEmptyOperand(operand));
}

export function findQueryBuilderItem(
    root: QueryBuilderGroup,
    itemId: string,
): QueryBuilderItem | null {
    if (root.id === itemId) {
        return root;
    }
    return findInContainer(root, itemId);
}

export function addRow(
    root: QueryBuilderGroup,
    containerId: string,
): { root: QueryBuilderGroup; rowId: string } {
    const rowId = crypto.randomUUID();
    const nextRoot = updateContainer(root, containerId, (container) => ({
        ...container,
        items: [
            ...container.items,
            {
                id: rowId,
                itemType: QUERY_BUILDER_ITEM_ROW,
                clause: emptyClause(itemsGraphSlug(container)),
            },
        ],
    }));
    return { root: nextRoot, rowId };
}

// A subgroup with the same ALL/ANY as its parent changes nothing, so a new one
// starts with the opposite.
export function addGroup(
    root: QueryBuilderGroup,
    containerId: string,
): { root: QueryBuilderGroup; groupId: string } {
    const groupId = crypto.randomUUID();
    const nextRoot = updateContainer(root, containerId, (container) => ({
        ...container,
        items: [
            ...container.items,
            {
                id: groupId,
                itemType: QUERY_BUILDER_ITEM_GROUP,
                graphSlug: itemsGraphSlug(container),
                logic: oppositeLogic(container.logic),
                label: "",
                items: [],
            },
        ],
    }));
    return { root: nextRoot, groupId };
}

export function addRelatedGroup(
    root: QueryBuilderGroup,
    containerId: string,
): { root: QueryBuilderGroup; groupId: string } {
    const groupId = crypto.randomUUID();
    const nextRoot = updateContainer(root, containerId, (container) => ({
        ...container,
        items: [
            ...container.items,
            {
                id: groupId,
                itemType: QUERY_BUILDER_ITEM_RELATED_GROUP,
                anchorGraphSlug: itemsGraphSlug(container),
                targetGraphSlug: "",
                relationship: {
                    path: {
                        type: ClauseSubjectTypeToken.NODE,
                        graph_slug: "",
                        node_alias: "",
                    },
                    is_inverse: false,
                    traversal_quantifier: QUANTIFIER_ANY,
                },
                logic: LogicToken.AND,
                label: "",
                items: [],
            },
        ],
    }));
    return { root: nextRoot, groupId };
}

export function removeQueryBuilderItem(
    root: QueryBuilderGroup,
    itemId: string,
): QueryBuilderGroup {
    return mapContainers(root, (container) => ({
        ...container,
        items: container.items.filter((item) => item.id !== itemId),
    }));
}

export function toggleGroupLogic(
    root: QueryBuilderGroup,
    containerId: string,
): QueryBuilderGroup {
    return updateContainer(root, containerId, (container) => ({
        ...container,
        logic: oppositeLogic(container.logic),
    }));
}

export function setGroupLabel(
    root: QueryBuilderGroup,
    containerId: string,
    label: string,
): QueryBuilderGroup {
    return updateContainer(root, containerId, (container) => ({
        ...container,
        label,
    }));
}

export function setRowClause(
    root: QueryBuilderGroup,
    rowId: string,
    clause: LiteralClause,
): QueryBuilderGroup {
    return updateRow(root, rowId, (row) => ({ ...row, clause }));
}

export function toggleRowNot(
    root: QueryBuilderGroup,
    rowId: string,
): QueryBuilderGroup {
    return updateRow(root, rowId, (row) => {
        let quantifier: LiteralClause["quantifier"] = QUANTIFIER_NONE;
        if (row.clause.quantifier === QUANTIFIER_NONE) {
            quantifier = QUANTIFIER_ANY;
        }
        return { ...row, clause: { ...row.clause, quantifier } };
    });
}

// Rows inside belong to the previous related model, so a new one starts over.
export function setRelatedTarget(
    root: QueryBuilderGroup,
    groupId: string,
    targetGraphSlug: string,
): QueryBuilderGroup {
    return updateRelatedGroup(root, groupId, (relatedGroup) => ({
        ...relatedGroup,
        targetGraphSlug,
        relationship: {
            ...relatedGroup.relationship,
            path: {
                ...relatedGroup.relationship.path,
                graph_slug: "",
                node_alias: "",
            },
        },
        items: [],
    }));
}

export function setRelatedRelationship(
    root: QueryBuilderGroup,
    groupId: string,
    relationship: RelationshipBlock,
): QueryBuilderGroup {
    return updateRelatedGroup(root, groupId, (relatedGroup) => ({
        ...relatedGroup,
        relationship,
    }));
}

export function toggleRelatedNot(
    root: QueryBuilderGroup,
    groupId: string,
): QueryBuilderGroup {
    return updateRelatedGroup(root, groupId, (relatedGroup) => {
        let traversalQuantifier: RelationshipBlock["traversal_quantifier"] =
            QUANTIFIER_NONE;
        if (
            relatedGroup.relationship.traversal_quantifier === QUANTIFIER_NONE
        ) {
            traversalQuantifier = QUANTIFIER_ANY;
        }
        return {
            ...relatedGroup,
            relationship: {
                ...relatedGroup.relationship,
                traversal_quantifier: traversalQuantifier,
            },
        };
    });
}

export function canGroupQueryBuilderItems(
    root: QueryBuilderGroup,
    itemIds: string[],
): boolean {
    return findGroupableParent(root, new Set(itemIds)) !== null;
}

// Wraps two or more items that share a parent in a new group, placed where the
// first of them was. Items from different parents cannot be grouped.
export function groupQueryBuilderItems(
    root: QueryBuilderGroup,
    itemIds: string[],
): { root: QueryBuilderGroup; groupId: string } | null {
    const selectedIds = new Set(itemIds);
    const parent = findGroupableParent(root, selectedIds);
    if (!parent) {
        return null;
    }

    const groupId = crypto.randomUUID();
    const nextRoot = updateContainer(root, parent.id, (container) => {
        const selectedItems = container.items.filter((item) =>
            selectedIds.has(item.id),
        );
        const firstSelectedIndex = container.items.findIndex((item) =>
            selectedIds.has(item.id),
        );
        const remainingItems = container.items.filter(
            (item) => !selectedIds.has(item.id),
        );
        const newGroup: QueryBuilderGroup = {
            id: groupId,
            itemType: QUERY_BUILDER_ITEM_GROUP,
            graphSlug: itemsGraphSlug(container),
            logic: oppositeLogic(container.logic),
            label: "",
            items: selectedItems,
        };
        return {
            ...container,
            items: [
                ...remainingItems.slice(0, firstSelectedIndex),
                newGroup,
                ...remainingItems.slice(firstSelectedIndex),
            ],
        };
    });
    return { root: nextRoot, groupId };
}

function plainGroupFromPayload(payload: GroupPayload): QueryBuilderGroup {
    return {
        id: crypto.randomUUID(),
        itemType: QUERY_BUILDER_ITEM_GROUP,
        graphSlug: payload.graph_slug,
        logic: payload.logic,
        label: payload.label ?? "",
        items: itemsFromPayload(payload, payload.graph_slug),
    };
}

function itemsFromPayload(
    payload: GroupPayload,
    graphSlug: string,
): QueryBuilderItem[] {
    const clauseItems: QueryBuilderItem[] = payload.clauses.map((clause) => {
        if (isEditableClause(clause)) {
            return {
                id: crypto.randomUUID(),
                itemType: QUERY_BUILDER_ITEM_ROW,
                clause,
            };
        }
        return {
            id: crypto.randomUUID(),
            itemType: QUERY_BUILDER_ITEM_LOCKED_CLAUSE,
            clause,
        };
    });

    const groupItems: QueryBuilderItem[] = payload.groups.map((subgroup) => {
        if (isEditablePlainGroup(subgroup, graphSlug)) {
            return plainGroupFromPayload(subgroup);
        }
        if (
            subgroup.relationship &&
            isEditableRelatedGroup(subgroup, graphSlug)
        ) {
            return relatedGroupFromPayload(subgroup, subgroup.relationship);
        }
        return lockedGroup(subgroup);
    });

    return [...clauseItems, ...groupItems];
}

function relatedGroupFromPayload(
    payload: GroupPayload,
    relationship: RelationshipBlock,
): QueryBuilderRelatedGroup {
    const innerGroup = payload.groups[0];
    return {
        id: crypto.randomUUID(),
        itemType: QUERY_BUILDER_ITEM_RELATED_GROUP,
        anchorGraphSlug: payload.graph_slug,
        targetGraphSlug: innerGroup.graph_slug,
        relationship,
        logic: innerGroup.logic,
        label: payload.label ?? "",
        items: itemsFromPayload(innerGroup, innerGroup.graph_slug),
    };
}

function lockedGroup(payload: GroupPayload): QueryBuilderItem {
    return {
        id: crypto.randomUUID(),
        itemType: QUERY_BUILDER_ITEM_LOCKED_GROUP,
        payload,
    };
}

function plainGroupToPayload(group: QueryBuilderGroup): GroupPayload {
    return withLabel(
        {
            graph_slug: group.graphSlug,
            scope: GraphScopeToken.RESOURCE,
            logic: group.logic,
            clauses: clausesOf(group.items),
            groups: groupsOf(group.items),
            aggregations: [],
            relationship: null,
        },
        group.label,
    );
}

function relatedGroupToPayload(
    relatedGroup: QueryBuilderRelatedGroup,
): GroupPayload {
    return withLabel(
        {
            graph_slug: relatedGroup.anchorGraphSlug,
            scope: GraphScopeToken.RESOURCE,
            logic: LogicToken.AND,
            clauses: [],
            groups: [
                {
                    graph_slug: relatedGroup.targetGraphSlug,
                    scope: GraphScopeToken.RESOURCE,
                    logic: relatedGroup.logic,
                    clauses: clausesOf(relatedGroup.items),
                    groups: groupsOf(relatedGroup.items),
                    aggregations: [],
                    relationship: null,
                },
            ],
            aggregations: [],
            relationship: relatedGroup.relationship,
        },
        relatedGroup.label,
    );
}

function withLabel(payload: GroupPayload, label: string): GroupPayload {
    if (!label) {
        return payload;
    }
    return { ...payload, label };
}

function clausesOf(items: QueryBuilderItem[]): LiteralClause[] {
    return items.flatMap((item) => {
        if (
            item.itemType === QUERY_BUILDER_ITEM_ROW ||
            item.itemType === QUERY_BUILDER_ITEM_LOCKED_CLAUSE
        ) {
            return [item.clause];
        }
        return [];
    });
}

function groupsOf(items: QueryBuilderItem[]): GroupPayload[] {
    return items.flatMap((item) => {
        if (item.itemType === QUERY_BUILDER_ITEM_GROUP) {
            return [plainGroupToPayload(item)];
        }
        if (item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP) {
            return [relatedGroupToPayload(item)];
        }
        if (item.itemType === QUERY_BUILDER_ITEM_LOCKED_GROUP) {
            return [item.payload];
        }
        return [];
    });
}

function pruneItems(
    items: QueryBuilderItem[],
    lookups: QueryBuilderLookups,
): QueryBuilderItem[] {
    return items.flatMap((item): QueryBuilderItem[] => {
        if (item.itemType === QUERY_BUILDER_ITEM_ROW) {
            if (isClauseComplete(item.clause, lookups)) {
                return [item];
            }
            return [];
        }
        if (item.itemType === QUERY_BUILDER_ITEM_GROUP) {
            const prunedItems = pruneItems(item.items, lookups);
            if (prunedItems.length === 0) {
                return [];
            }
            return [{ ...item, items: prunedItems }];
        }
        if (item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP) {
            if (!isRelationshipComplete(item)) {
                return [];
            }
            return [{ ...item, items: pruneItems(item.items, lookups) }];
        }
        return [item];
    });
}

function isRelationshipComplete(
    relatedGroup: QueryBuilderRelatedGroup,
): boolean {
    return Boolean(
        relatedGroup.targetGraphSlug &&
            relatedGroup.relationship.path.graph_slug &&
            relatedGroup.relationship.path.node_alias,
    );
}

function isEmptyOperand(operand: LiteralOperand | undefined): boolean {
    if (!operand) {
        return true;
    }
    const value = operand.value;
    if (value === null || value === undefined || value === "") {
        return true;
    }
    if (Array.isArray(value)) {
        return value.length === 0;
    }
    if (typeof value === "object" && "features" in value) {
        return !Array.isArray(value.features) || value.features.length === 0;
    }
    return false;
}

function searchModelsDatatype(searchModels: string[]): string | undefined {
    if (searchModels.includes(SEARCH_MODEL_GEOMETRY)) {
        return DATATYPE_GEOJSON;
    }
    if (searchModels.some((model) => SEARCH_MODELS_DATE.includes(model))) {
        return DATATYPE_DATE;
    }
    if (searchModels.includes(SEARCH_MODEL_TERM)) {
        return DATATYPE_STRING;
    }
    return undefined;
}

function isEditableClause(clause: LiteralClause): boolean {
    const clauseType: string = clause.type;
    if (clauseType !== CLAUSE_TYPE_LITERAL) {
        return false;
    }
    const subjectType: string = clause.subject.type;
    if (subjectType === ClauseSubjectTypeToken.NODE) {
        return true;
    }
    if (subjectType !== ClauseSubjectTypeToken.SEARCH_MODELS) {
        return false;
    }
    const searchModels = clause.subject.search_models;
    const isGeometry =
        searchModels.length === 1 && searchModels[0] === SEARCH_MODEL_GEOMETRY;
    const isText =
        searchModels.length === 1 && searchModels[0] === SEARCH_MODEL_TERM;
    const isDate =
        searchModels.length > 0 &&
        searchModels.every((model) => SEARCH_MODELS_DATE.includes(model));
    return isGeometry || isDate || isText;
}

function isEditableGroupShape(payload: GroupPayload): boolean {
    return (
        payload.scope === GraphScopeToken.RESOURCE &&
        payload.aggregations.length === 0
    );
}

function isEditablePlainGroup(
    payload: GroupPayload,
    parentGraphSlug: string,
): boolean {
    return (
        payload.relationship === null &&
        payload.graph_slug === parentGraphSlug &&
        isEditableGroupShape(payload)
    );
}

function isEditableRelatedGroup(
    payload: GroupPayload,
    parentGraphSlug: string,
): boolean {
    if (
        payload.graph_slug !== parentGraphSlug ||
        payload.clauses.length > 0 ||
        payload.groups.length !== 1 ||
        !isEditableGroupShape(payload)
    ) {
        return false;
    }
    const innerGroup = payload.groups[0];
    return innerGroup.relationship === null && isEditableGroupShape(innerGroup);
}

function emptyClause(graphSlug: string): LiteralClause {
    return {
        type: CLAUSE_TYPE_LITERAL,
        quantifier: QUANTIFIER_ANY,
        subject: {
            type: ClauseSubjectTypeToken.NODE,
            graph_slug: graphSlug,
            node_alias: "",
            search_models: [],
        },
        operator: null,
        operands: [],
    };
}

function oppositeLogic(logic: LogicToken): LogicToken {
    if (logic === LogicToken.AND) {
        return LogicToken.OR;
    }
    return LogicToken.AND;
}

function isContainer(item: QueryBuilderItem): item is QueryBuilderContainer {
    return (
        item.itemType === QUERY_BUILDER_ITEM_GROUP ||
        item.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP
    );
}

function itemsGraphSlug(container: QueryBuilderContainer): string {
    if (container.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP) {
        return container.targetGraphSlug;
    }
    return container.graphSlug;
}

function findInContainer(
    container: QueryBuilderContainer,
    itemId: string,
): QueryBuilderItem | null {
    for (const item of container.items) {
        if (item.id === itemId) {
            return item;
        }
        if (isContainer(item)) {
            const found = findInContainer(item, itemId);
            if (found) {
                return found;
            }
        }
    }
    return null;
}

function findGroupableParent(
    root: QueryBuilderGroup,
    selectedIds: Set<string>,
): QueryBuilderContainer | null {
    if (selectedIds.size < MINIMUM_ITEMS_TO_GROUP) {
        return null;
    }
    return findContainerHoldingAll(root, selectedIds);
}

function findContainerHoldingAll(
    container: QueryBuilderContainer,
    itemIds: Set<string>,
): QueryBuilderContainer | null {
    const heldCount = container.items.filter((item) =>
        itemIds.has(item.id),
    ).length;
    if (heldCount === itemIds.size) {
        return container;
    }
    if (heldCount > 0) {
        return null;
    }
    for (const item of container.items) {
        if (isContainer(item)) {
            const found = findContainerHoldingAll(item, itemIds);
            if (found) {
                return found;
            }
        }
    }
    return null;
}

// The root is always a plain group, so of a transformed root only what a
// plain group's transform can change is taken back.
function mapContainers(
    root: QueryBuilderGroup,
    transform: (container: QueryBuilderContainer) => QueryBuilderContainer,
): QueryBuilderGroup {
    function visitItem(item: QueryBuilderItem): QueryBuilderItem {
        if (!isContainer(item)) {
            return item;
        }
        const transformed = transform(item);
        return { ...transformed, items: transformed.items.map(visitItem) };
    }

    const transformedRoot = transform(root);
    return {
        ...root,
        logic: transformedRoot.logic,
        label: transformedRoot.label,
        items: transformedRoot.items.map(visitItem),
    };
}

function updateContainer(
    root: QueryBuilderGroup,
    containerId: string,
    transform: (container: QueryBuilderContainer) => QueryBuilderContainer,
): QueryBuilderGroup {
    return mapContainers(root, (container) => {
        if (container.id === containerId) {
            return transform(container);
        }
        return container;
    });
}

function updateRelatedGroup(
    root: QueryBuilderGroup,
    groupId: string,
    transform: (
        relatedGroup: QueryBuilderRelatedGroup,
    ) => QueryBuilderRelatedGroup,
): QueryBuilderGroup {
    return mapContainers(root, (container) => {
        if (
            container.id === groupId &&
            container.itemType === QUERY_BUILDER_ITEM_RELATED_GROUP
        ) {
            return transform(container);
        }
        return container;
    });
}

function updateRow(
    root: QueryBuilderGroup,
    rowId: string,
    transform: (row: QueryBuilderRow) => QueryBuilderRow,
): QueryBuilderGroup {
    return mapContainers(root, (container) => ({
        ...container,
        items: container.items.map((item) => {
            if (item.id === rowId && item.itemType === QUERY_BUILDER_ITEM_ROW) {
                return transform(item);
            }
            return item;
        }),
    }));
}
