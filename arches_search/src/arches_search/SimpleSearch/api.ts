import arches from "arches";
import Cookies from "js-cookie";

import type { SearchResults } from "@/arches_search/AdvancedSearch/types.ts";
import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

interface TermFilter {
    type: "term" | "concept" | "string";
    value: string;
    text: string;
    inverted: boolean;
}

export async function fetchSimpleSearchResults({
    terms = [],
    graphId = null,
    page = 1,
}: {
    terms?: TermFilter[];
    graphId?: string | null;
    page?: number;
} = {}): Promise<SearchResults> {
    const body: Record<string, unknown> = {};

    if (terms.length > 0) {
        body["term-filter"] = terms;
    }

    if (graphId) {
        body["typeFilter"] = { graphid: graphId, inverted: false };
    }

    if (page > 1) {
        body["paging-filter"] = page;
    }

    const response = await fetch(arches.urls["api-search"], {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken") || "",
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        throw new Error(response.statusText);
    }

    const data = await response.json();

    const pageSize: number = data.page_size || 25;
    const total: number = data.total_results || 0;
    const totalPages = Math.ceil(total / pageSize);

    const resources = (data.results || []).map(
        (hit: Record<string, unknown>) => {
            const source =
                (hit._source as Record<string, unknown> | undefined) || hit;
            return {
                resourceinstanceid: source.resourceinstanceid as string,
                graph_id: source.graph_id as string,
                createdtime: (source.createdtime as string) || "",
            };
        },
    );

    return {
        resources,
        aggregations: (data.aggregations as Record<string, unknown>) || {},
        pagination: {
            page,
            page_size: pageSize,
            total_results: total,
            total_pages: totalPages,
            has_next: page < totalPages,
            has_previous: page > 1,
        },
    };
}

export async function fetchSearchTermSuggestions(
    query: string,
): Promise<Array<{ text: string; datatype: string; value: string }>> {
    const params = new URLSearchParams({ q: query, lang: "*", flat: "true" });
    const response = await fetch(
        `${generateArchesURL("arches_search:term_suggestion_search")}?${params.toString()}`,
    );
    const results = await response.json();
    const suggestions = results.results as Array<{
        text: string;
        datatype: string;
        value: string;
    }>;

    // Prepend a literal term entry for the raw query string
    suggestions.unshift({ text: query, datatype: "term", value: query });

    return suggestions;
}
