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

export interface ResourceInstanceLifecycleState {
    id: string;
    name: string;
    action_label: string;
    is_initial_state: boolean;
    can_delete_resource_instances: boolean;
    can_edit_resource_instances: boolean;
}
