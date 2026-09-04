import Cookies from "js-cookie";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import { generateArchesURL } from "@/arches_vue_components/application";

export async function getSearchResults(
    searchQuery: GroupPayload,
    options?: { page?: number; pageSize?: number },
) {
    const requestPayload: {
        graph_slugs: string[];
        advanced_search_queries: GroupPayload[];
        page?: number;
        page_size?: number;
    } = {
        graph_slugs: [searchQuery.graph_slug],
        advanced_search_queries: [searchQuery],
    };

    if (options && options.page !== undefined) {
        requestPayload.page = options.page;
    }

    if (options && options.pageSize !== undefined) {
        requestPayload.page_size = options.pageSize;
    }

    const url = generateArchesURL("arches_search:search");

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken") || "",
        },
        body: JSON.stringify(requestPayload),
    });

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
}

export async function getSearchSQL(searchQuery: GroupPayload) {
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

export async function getNodeMetadataForPayload(payload: GroupPayload) {
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

export async function getResourceNamesForPayload(payload: GroupPayload) {
    const response = await fetch(
        generateArchesURL("arches_search:resource_names_for_payload"),
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

export async function getRelatableNodesTreeForGraphId(graphId: string) {
    const response = await fetch(
        generateArchesURL("arches_search:api-relatable-nodes-tree-for-graph", {
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

export async function getRelatableNodesTreeForGraphPair(
    graphId: string,
    otherGraphId: string,
) {
    const response = await fetch(
        generateArchesURL(
            "arches_search:api-relatable-nodes-tree-for-graph-pair",
            {
                graph_id: graphId,
                other_graph_id: otherGraphId,
            },
        ),
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

export async function getDateBoundsForGraphId(
    graphId: string,
    nodeAliases: string[] = [],
): Promise<{ min_value: number | null; max_value: number | null }> {
    const baseUrl = generateArchesURL(
        "arches_search:node_date_bounds_for_graph",
        { graph_id: graphId },
    );

    let url = baseUrl;
    if (nodeAliases.length > 0) {
        const params = new URLSearchParams();
        for (const alias of nodeAliases) {
            params.append("node_alias", alias);
        }
        url = `${baseUrl}?${params.toString()}`;
    }

    const response = await fetch(url, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
    });

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
