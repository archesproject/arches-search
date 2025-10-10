import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

export async function getSearchResults(searchQuery: {
    [key: string]: unknown;
}) {
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

export async function getNodes(graphId: string) {
    const response = await fetch(
        generateArchesURL("arches:graph_nodes", { graphid: graphId }),
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
