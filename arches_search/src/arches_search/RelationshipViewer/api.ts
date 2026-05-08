import arches from "arches";
import type { GraphData } from "@/arches_search/RelationshipViewer/types.ts";

export interface RelationshipViewerParams {
    resourceIds: string[];
    depth?: 1 | 2;
    relationshipTypes?: string[];
}

export async function fetchRelationshipGraph(
    params: RelationshipViewerParams,
): Promise<GraphData> {
    const qs = new URLSearchParams();
    qs.set("resource_ids", params.resourceIds.join(","));
    qs.set("depth", String(params.depth ?? 1));
    for (const rt of params.relationshipTypes ?? []) {
        qs.append("relationship_types", rt);
    }
    const response = await fetch(
        `${arches.urls["api_relationship_viewer"]}?${qs.toString()}`,
    );
    if (!response.ok) {
        throw new Error(`Relationship viewer API error: ${response.statusText}`);
    }
    return response.json() as Promise<GraphData>;
}
