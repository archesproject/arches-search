export interface AdvancedSearchFacet {
    id: number;
    arity: number;
    datatype_id: string;
    is_orm_template_negated: boolean;
    label: string;
    operator: string;
    orm_template: string;
    param_formats: string[];
    sortorder: number;
}

export interface GraphModel {
    author: string;
    color: string | null;
    config: Record<string, unknown>;
    deploymentdate: string | null;
    deploymentfile: string | null;
    description: string;
    disable_instance_creation: boolean;
    functions: unknown[];
    graphid: string;
    has_unpublished_changes: boolean;
    iconclass: string;
    is_active: boolean;
    is_copy_immutable: boolean;
    isresource: boolean;
    jsonldcontext: string | null;
    name: string;
    ontology_id: string | null;
    publication_id: string | null;
    resource_instance_lifecycle_id: string | null;
    slug: string;
    source_identifier_id: number | null;
    subtitle: string;
    template_id: string | null;
    version: string;
}

export interface Node {
    alias: string;
    config: Record<string, unknown>;
    datatype: string;
    description: string | null;
    exportable: boolean;
    fieldname: string | null;
    graph_id: string;
    hascustomalias: boolean;
    is_collector: boolean;
    is_immutable: boolean;
    isrequired: boolean;
    issearchable: boolean;
    istopnode: boolean;
    name: string;
    nodegroup_id: string;
    nodeid: string;
    ontologyclass: string | null;
    // False for a card heading listed beside its top node, under the same alias.
    selectable?: boolean;
    card_x_node_x_widget_label?: string;
    nodegroup_has_cardinality_n?: boolean;
    sortorder: number;
    source_identifier_id: number | null;
    sourcebranchpublication_id: string | null;
}

export enum GraphScopeToken {
    RESOURCE = "RESOURCE",
    TILE = "TILE",
}

export enum LogicToken {
    AND = "AND",
    OR = "OR",
}

export enum ClauseSubjectTypeToken {
    NODE = "NODE",
    SEARCH_MODELS = "SEARCH_MODELS",
}

type ClauseTypeToken = "LITERAL";
type QuantifierToken = "ANY" | "ALL" | "NONE";

export type OperatorString = string;

export type SubjectPair = [graphSlug: string, nodeAlias: string];
export type SubjectPath = SubjectPair[];
export type PathSelection = {
    graph_slug: string;
    node_alias: string;
    // Disambiguates a self-relationship's two identically-slugged/aliased branches.
    is_inverse?: boolean;
};
export type ClauseSubject = {
    type: ClauseSubjectTypeToken;
    graph_slug: string;
    node_alias: string;
    search_models: string[];
};
export type RelationshipPath = {
    type: ClauseSubjectTypeToken.NODE;
    graph_slug: string;
    node_alias: string;
};

export type LiteralOperand = {
    type: "LITERAL";
    value: unknown;
    display_value?: string;
};

export type LiteralClause = {
    type: ClauseTypeToken;
    quantifier: QuantifierToken;
    subject: ClauseSubject;
    operator: OperatorString | null;
    operands: LiteralOperand[];
};

export type RelationshipBlock = {
    path: RelationshipPath;
    is_inverse: boolean;
    traversal_quantifier: QuantifierToken;
};

export type GroupPayload = {
    graph_slug: string;
    scope: GraphScopeToken;
    logic: LogicToken;
    clauses: LiteralClause[];
    groups: GroupPayload[];
    aggregations: unknown[];
    relationship: RelationshipBlock | null;
    // Display only; the backend ignores it.
    label?: string;
};

export const SEARCH_MODEL_GEOMETRY = "GeometrySearch";
export const SEARCH_MODEL_TERM = "TermSearch";
export const SEARCH_MODELS_DATE = ["DateSearch", "DateRangeSearch"];

export const QUERY_BUILDER_ITEM_ROW = "row";
export const QUERY_BUILDER_ITEM_GROUP = "group";
export const QUERY_BUILDER_ITEM_RELATED_GROUP = "related-group";
export const QUERY_BUILDER_ITEM_LOCKED_CLAUSE = "locked-clause";
export const QUERY_BUILDER_ITEM_LOCKED_GROUP = "locked-group";

export type QueryBuilderRow = {
    id: string;
    itemType: typeof QUERY_BUILDER_ITEM_ROW;
    clause: LiteralClause;
};

export type QueryBuilderGroup = {
    id: string;
    itemType: typeof QUERY_BUILDER_ITEM_GROUP;
    graphSlug: string;
    logic: LogicToken;
    label: string;
    items: QueryBuilderItem[];
};

// Rows inside a related group filter the related resource, so they are on
// targetGraphSlug; the group itself sits among its parent's anchorGraphSlug
// items. `logic` is the ALL/ANY of those inner rows.
export type QueryBuilderRelatedGroup = {
    id: string;
    itemType: typeof QUERY_BUILDER_ITEM_RELATED_GROUP;
    anchorGraphSlug: string;
    targetGraphSlug: string;
    relationship: RelationshipBlock;
    logic: LogicToken;
    label: string;
    targetLabel: string;
    items: QueryBuilderItem[];
};

// Parts of a saved query the builder cannot edit are carried as they are, so
// loading and re-saving a query never loses or changes them.
export type QueryBuilderLockedClause = {
    id: string;
    itemType: typeof QUERY_BUILDER_ITEM_LOCKED_CLAUSE;
    clause: LiteralClause;
};

export type QueryBuilderLockedGroup = {
    id: string;
    itemType: typeof QUERY_BUILDER_ITEM_LOCKED_GROUP;
    payload: GroupPayload;
};

export type QueryBuilderItem =
    | QueryBuilderRow
    | QueryBuilderGroup
    | QueryBuilderRelatedGroup
    | QueryBuilderLockedClause
    | QueryBuilderLockedGroup;

export interface AdvancedSearchOperandComponent {
    datatype_id: string;
    slug: string;
    label: string;
    icon: string;
    component: string;
    sets_operator: boolean;
}

export interface QueryBuilderLookups {
    getNodeDatatype(graphSlug: string, nodeAlias: string): string | undefined;
    getOperatorArity(datatype: string, operator: string): number | undefined;
    getOperandComponent(
        datatype: string,
    ): AdvancedSearchOperandComponent | undefined;
}

export type NodeMetadataEntry = {
    card_x_node_x_widget_label?: string;
    datatype?: string;
};

export type NodeMetadataMap = Readonly<Record<string, NodeMetadataEntry>>;

export type RelatableNodeOption = {
    key: string;
    label: string;
    children: RelatableNodeOption[];
    data: {
        id: string;
        graph_id: string;
        alias: string;
        name: string;
        description: string;
        datatype: string;
        is_inverse: boolean;
    };
};

export type RelatableGraphOption = {
    key: string;
    label: string;
    children: RelatableNodeOption[];
    data: {
        graph_id: string;
        slug: string;
        name: string;
    };
};

export type RelatableNodesTreeResponse = {
    target_graph_id: string;
    relatable_graphs: { graph_id: string; slug: string; name: string }[];
    options: RelatableGraphOption[];
};

export type RelatableNodesTreeForGraphPairResponse = {
    options: RelatableGraphOption[];
};

export interface ResourceTypeCount {
    graph_id: string;
    name: string;
    icon: string;
    count: number;
}

export type SearchResults = {
    resources: ResourceData[];
    aggregations: { [key: string]: unknown };
    pagination: {
        page: number;
        page_size: number;
        total_results: number;
        total_pages: number;
        has_next: boolean;
        has_previous: boolean;
    };
    resource_type_counts?: ResourceTypeCount[];
};

export interface ResourceData {
    resourceinstanceid: string;
    name?: string;
    descriptors?: {
        [key: string]: {
            name: string;
            map_popup: string;
            description: string;
        };
    };
    legacyid?: string | null;
    createdtime: string;
    graph_id: string;
    graph_publication_id?: string;
    principaluser_id?: number;
    resource_instance_lifecycle_state_id?: string | null;
}
