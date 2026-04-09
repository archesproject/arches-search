export interface ResourceType {
    id: string | null; // graph id; null = "all types"
    label: string;
    icon: string;
}

export interface ActiveFilter {
    id: string;
    label: string;
    clear: () => void;
    options?: Record<string, unknown>;
}

export interface SortOption {
    label: string;
    value: string;
}

export interface AttributeFilterOption {
    id: string;
    label: string;
    count?: number;
}

export interface AttributeFilterSection {
    id: string;
    label: string;
    options: AttributeFilterOption[];
}
