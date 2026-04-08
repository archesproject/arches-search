import Cookies from "js-cookie";

import type { SearchResults } from "@/arches_search/AdvancedSearch/types.ts";
import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";
import type { GroupPayload } from "../AdvancedSearch/types";

interface TermFilter {
    type: "term" | "concept" | "string";
    value: string;
    text: string;
    inverted: boolean;
}

export async function fetchSearchResults({
    terms = [],
    query = {} as GroupPayload,
    graphId = null,
    page = 1,
}: {
    terms?: TermFilter[];
    query?: GroupPayload;
    graphId?: string | null;
    page?: number;
} = {}): Promise<SearchResults> {

    const requestPayload = {
        graphId: graphId,
        terms: terms,
        query: query,
    };

    const response = await fetch(
        `${generateArchesURL("arches_search:simple_search")}`,
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

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
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
