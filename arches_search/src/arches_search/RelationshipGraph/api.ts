import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches_vue_components/application";

import type {
    RelationshipGraphData,
    RelationshipPath,
    RelationshipSummary,
    RowSelection,
} from "@/arches_search/RelationshipGraph/types.ts";

async function parseResponse<T>(response: Response): Promise<T> {
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
}

export async function fetchRelationshipSummary(
    resourceId: string,
): Promise<RelationshipSummary> {
    const params = new URLSearchParams({ resource_id: resourceId });
    const url =
        generateArchesURL("arches_search:relationship_graph_summary") +
        "?" +
        params.toString();

    return parseResponse(await fetch(url));
}

export async function fetchRelationshipPath(
    fromResourceId: string,
    toResourceId: string,
): Promise<RelationshipPath> {
    const params = new URLSearchParams({
        from: fromResourceId,
        to: toResourceId,
    });
    const url =
        generateArchesURL("arches_search:relationship_graph_path") +
        "?" +
        params.toString();

    return parseResponse(await fetch(url));
}

export async function fetchRelationshipGraph(
    selections: RowSelection[],
    pathRelationshipIds: string[],
): Promise<RelationshipGraphData> {
    return parseResponse(
        await fetch(generateArchesURL("arches_search:relationship_graph"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify({
                selections,
                path_relationship_ids: pathRelationshipIds,
            }),
        }),
    );
}
