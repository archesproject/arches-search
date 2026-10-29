import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches_vue_components/application";

import type {
    RelationshipGraphData,
    RelationshipSummary,
    RowSelection,
} from "@/arches_search/RelationshipGraph/types.ts";

export async function fetchRelationshipSummary(
    resourceId: string,
): Promise<RelationshipSummary> {
    const params = new URLSearchParams({ resource_id: resourceId });
    const url =
        generateArchesURL("arches_search:relationship_graph_summary") +
        "?" +
        params.toString();

    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
}

export async function fetchRelationshipGraph(
    selections: RowSelection[],
): Promise<RelationshipGraphData> {
    const response = await fetch(
        generateArchesURL("arches_search:relationship_graph"),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify({ selections }),
        },
    );
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
}
