import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches_vue_components/application";

import type {
    ResourceTypeCount,
    SearchDefinitionCountRequest,
} from "@/arches_search/SearchLanding/types.ts";

export async function fetchResourceTypeCounts(): Promise<ResourceTypeCount[]> {
    const response = await fetch(
        generateArchesURL("arches_search:resource_type_counts"),
    );
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    const data = (await response.json()) as {
        resourceTypes: ResourceTypeCount[];
    };
    return data.resourceTypes;
}

export async function fetchSearchDefinitionCounts(
    items: SearchDefinitionCountRequest[],
): Promise<Record<string, number | null>> {
    const response = await fetch(
        generateArchesURL("arches_search:search_definition_counts"),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify({ items }),
        },
    );
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    const data = (await response.json()) as {
        counts: Record<string, number | null>;
    };
    return data.counts;
}
