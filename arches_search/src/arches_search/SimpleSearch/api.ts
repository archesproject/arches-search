import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import type { TermSuggestion } from "@/arches_search/SimpleSearch/types.ts";

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
