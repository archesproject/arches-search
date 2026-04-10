export type TimeFilterNodeSummary = {
    id: string;
    alias: string;
    name: string;
    datatype: string;
    sortorder: number;
    card_x_node_x_widget_label?: string;
    semantic_parent_id: string | null;
    selectable?: boolean;
    graph_id?: string;
    config?: unknown;
    [key: string]: unknown;
};

export type TimeFilterTreeNode = {
    key: string;
    label: string;
    data: TimeFilterNodeSummary;
    children: TimeFilterTreeNode[];
    selectable?: boolean;
};
