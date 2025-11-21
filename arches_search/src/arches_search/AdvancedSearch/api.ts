import Cookies from "js-cookie";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

export async function getSearchResults(searchQuery: GroupPayload) {
    const response = await fetch(
        generateArchesURL("arches_search:advanced_search"),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify(searchQuery),
        },
    );

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
}

export async function getSearchSQL(searchQuery: { [key: string]: unknown }) {
    const response = await fetch(
        generateArchesURL("arches_search:advanced_search_sql"),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify(searchQuery),
        },
    );

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
}

export async function getNodeMetadataForPayload(payload: {
    [key: string]: unknown;
}) {
    const response = await fetch(
        generateArchesURL("arches_search:node_metadata_for_payload"),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify(payload),
        },
    );

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
}

export async function getNodesForGraphId(graphId: string) {
    const response = await fetch(
        generateArchesURL("arches_search:nodes_with_widget_labels_for_graph", {
            graph_id: graphId,
        }),
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        },
    );

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
}

export async function getAdvancedSearchFacets() {
    const response = await fetch(
        generateArchesURL("arches_search:all_datatype_facets"),
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        },
    );

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
}

export async function getGraphs() {
    const response = await fetch(
        generateArchesURL("arches_search:graph_models"),
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        },
    );

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
}

export async function getThumbnailExists(resourceIdentifier: string) {
    const response = await fetch(
        generateArchesURL("arches:thumbnail", {
            resource_id: resourceIdentifier,
        }),
        { method: "HEAD" },
    );

    return response.ok;
}
