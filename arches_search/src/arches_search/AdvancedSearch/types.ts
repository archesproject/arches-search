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
    sql_template: string;
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
