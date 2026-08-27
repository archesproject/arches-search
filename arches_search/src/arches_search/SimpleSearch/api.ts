import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches_vue_components/application";
import { getItemLabel } from "@/arches_controlled_lists/utils.ts";

import type { ControlledListItem } from "@/arches_controlled_lists/types.ts";
import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    NodeFilterConfigResponse,
    SavedSearch,
    SortSpec,
    TermSuggestion,
} from "@/arches_search/SimpleSearch/types.ts";
import type { FeatureCollection } from "geojson";

export async function createSearchMVTContext(params: {
    terms?: { type: string; text: string; inverted: boolean }[];
    query?: GroupPayload;
    graphIds?: string[];
    mapFilter?: FeatureCollection | null;
}): Promise<{ context_id: string }> {
    const url = generateArchesURL("arches_search:search_mvt_context");
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken") || "",
        },
        body: JSON.stringify(params),
    });
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    return await response.json();
}

export async function fetchSearchResults({
    terms = [],
    query = {} as GroupPayload,
    graphIds = [],
    mapFilter = null,
    page = 1,
    sort,
}: {
    terms?: { type: string; text: string; inverted: boolean }[];
    query?: GroupPayload;
    graphIds?: string[];
    mapFilter?: FeatureCollection | null;
    page?: number;
    sort?: SortSpec[];
} = {}): Promise<SearchResults> {
    const requestPayload: Record<string, unknown> = {
        graphIds: graphIds,
        terms: terms,
        query: query,
        mapFilter: mapFilter,
        page: page,
    };

    if (sort !== undefined) {
        requestPayload.sort = sort;
    }

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
    language: string,
    systemLanguage: string,
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
    return (data.items as ControlledListItem[])
        .filter((item) => !item.guide)
        .map((item) => {
            return {
                id: item.id,
                label: getItemLabel(item, language, systemLanguage).value,
                uri: item.uri,
                sortorder: item.sortorder,
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

export async function getSavedSearches(
    scope: "mine" | "shared" = "mine",
    search = "",
): Promise<SavedSearch[]> {
    const params = new URLSearchParams({ scope });
    if (search) {
        params.set("search", search);
    }
    const response = await fetch(
        `${generateArchesURL("arches_search:saved_searches")}?${params.toString()}`,
    );
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    return response.json();
}

export async function createSavedSearch(
    name: string,
    description: string,
    queryDefinition: Record<string, unknown>,
): Promise<SavedSearch> {
    const response = await fetch(
        generateArchesURL("arches_search:saved_searches"),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify({
                name,
                description,
                query_definition: queryDefinition,
            }),
        },
    );
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    return response.json();
}

export async function deleteSavedSearch(savedsearchid: string): Promise<void> {
    const response = await fetch(
        `${generateArchesURL("arches_search:saved_searches")}/${savedsearchid}`,
        {
            method: "DELETE",
            headers: {
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
        },
    );
    if (!response.ok) {
        throw new Error(response.statusText);
    }
}

export async function exportSearchResults({
    terms = [],
    query,
    graphIds = [],
    filename = "search_export",
    allDescriptors = false,
}: {
    terms?: { type: string; text: string; inverted: boolean }[];
    query?: GroupPayload;
    graphIds?: string[];
    filename?: string;
    allDescriptors?: boolean;
}): Promise<void> {
    const response = await fetch(
        generateArchesURL("arches_search:search_export"),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": Cookies.get("csrftoken") || "",
            },
            body: JSON.stringify({
                terms,
                query,
                graphIds,
                filename,
                allDescriptors,
            }),
        },
    );

    if (!response.ok) {
        throw new Error(response.statusText);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    window.URL.revokeObjectURL(url);
}
