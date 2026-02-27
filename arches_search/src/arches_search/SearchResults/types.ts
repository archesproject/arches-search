export interface SearchReportConfig {
    name: string;
    theme: string;
    components: SearchReportConfigComponent[];
}

export interface SearchReportConfigComponent {
    component: string;
    config: Record<string, unknown>;
}

export interface ResourceDescriptorData {
    descriptors: Record<
        string,
        {
            name: string;
            description: string;
            map_popup: string;
        }
    >;
    graph_id: string;
}
