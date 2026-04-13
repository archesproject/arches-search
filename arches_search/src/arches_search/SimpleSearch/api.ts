import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";


import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    NodeFilterConfigResponse,
    TermSuggestion,
} from "@/arches_search/SimpleSearch/types.ts";

export async function fetchSearchResults({
    terms = [],
    query = {} as GroupPayload,
    graphId = null,
    page = 1,
}: {
    terms?: { type: string; text: string; inverted: boolean }[];
    query?: GroupPayload;
    graphId?: string | null;
    page?: number;
} = {}): Promise<SearchResults> {
    const requestPayload = {
        graphId: graphId,
        terms: terms,
        query: query,
        page: page,
    };

    const response = await fetch(
        `${generateArchesURL("arches_search:arches_search")}`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify(requestPayload),
        },
    );

    if (!response.ok) {
        throw new Error(response.statusText);
    }

    return await response.json();
}

export async function fetchNodeFilterConfig(
    graphId: string,
    slug = "filtering",
): Promise<NodeFilterConfigResponse> {
    const params = new URLSearchParams({ slug });
    const response = await fetch(
        `${generateArchesURL("arches_search:node_filter_config_for_graph", { graph_id: graphId })}?${params.toString()}`,
    );
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    return response.json();
}

export async function fetchControlledListItems(
    listId: string,
): Promise<
    Array<{ id: string; label: string; uri: string; sortorder: number }>
> {
    const response = await fetch(
        `${generateArchesURL("arches_controlled_lists:controlled_list", { list_id: listId })}?flat=true`,
    );
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    const data = await response.json();
    return (data.items as Array<Record<string, unknown>>)
        .filter((item: Record<string, unknown>) => !item.guide)
        .map((item: Record<string, unknown>) => {
            const values = item.values as Array<{
                valuetype_id: string;
                language_id: string;
                value: string;
            }>;
            const prefLabel = values.find(
                (v) => v.valuetype_id === "prefLabel",
            );
            return {
                id: item.id as string,
                label: prefLabel?.value ?? (item.uri as string),
                uri: item.uri as string,
                sortorder: item.sortorder as number,
            };
        });
}

export async function fetchSearchTermSuggestions(
    query: string,
): Promise<TermSuggestion[]> {
    const params = new URLSearchParams({ q: query, lang: "*", flat: "true" });
    const response = await fetch(
        `${generateArchesURL("arches_search:term_suggestion_search")}?${params.toString()}`,
    );
    const results = await response.json();
    const suggestions = results.results as Array<TermSuggestion>;

    // Prepend a literal term entry for the raw query string
    suggestions.unshift({ id: Date.now(), datatype: "term", text: query });

    return suggestions;
}
