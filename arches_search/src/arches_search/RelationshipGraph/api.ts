import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches_vue_components/application";

import type {
    RelationshipGraphData,
    RelationshipPath,
    RelationshipSummary,
    RelatedResourcesPage,
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
    const url = generateArchesURL(
        "arches_search:relationship_graph_summary",
        {},
        { resource_id: resourceId },
    );

    return parseResponse(await fetch(url));
}

export async function fetchRelationshipPath(
    fromResourceId: string,
    toResourceId: string,
): Promise<RelationshipPath> {
    const url = generateArchesURL(
        "arches_search:relationship_graph_path",
        {},
        { from: fromResourceId, to: toResourceId },
    );

    return parseResponse(await fetch(url));
}

export async function fetchRelatedResources(
    resourceId: string,
    rowId: string,
    offset: number,
    limit: number,
    term: string,
): Promise<RelatedResourcesPage> {
    const url = generateArchesURL(
        "arches_search:relationship_graph_related_resources",
        {},
        { resource_id: resourceId, row_id: rowId, offset, limit, term },
    );

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
