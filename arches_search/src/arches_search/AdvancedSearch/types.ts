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

type ClauseTypeToken = "LITERAL";
type QuantifierToken = "ANY";

export type OperatorString = string;

export type SubjectPair = [graphSlug: string, nodeAlias: string];
export type SubjectPath = ReadonlyArray<SubjectPair>;
export type RelationshipPath = ReadonlyArray<SubjectPair>;

export type LiteralOperand = {
    type: "LITERAL";
    value: unknown;
};

export type LiteralClause = {
    type: ClauseTypeToken;
    quantifier: QuantifierToken;
    subject: SubjectPath;
    operator: OperatorString;
    operands: ReadonlyArray<LiteralOperand>;
};

export type RelationshipBlock = {
    path: RelationshipPath;
    is_inverse: boolean;
    traversal_quantifiers: ReadonlyArray<QuantifierToken>;
};

export type GroupPayload = {
    graph_slug: string;
    scope: GraphScopeToken;
    logic: LogicToken;
    clauses: ReadonlyArray<LiteralClause>;
    groups: ReadonlyArray<GroupPayload>;
    aggregations: ReadonlyArray<unknown>;
    relationship: RelationshipBlock | null;
};

export type SearchResults = {
    resources: ResourceData[];
    aggregations: { [key: string]: unknown };
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
