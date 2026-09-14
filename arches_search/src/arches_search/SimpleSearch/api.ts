import Cookies from "js-cookie";

import { generateArchesURL } from "@/arches_vue_components/application";
import { getItemLabel } from "@/arches_controlled_lists/utils.ts";
import { buildSearchApiRequestBody } from "@/arches_search/SimpleSearch/utils/search-payload-builder.ts";

import type { FeatureCollection } from "geojson";

import type { ControlledListItem } from "@/arches_controlled_lists/types.ts";
import type {
    GroupPayload,
    SearchResults,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    DateRangeFilter,
    NodeFilterConfigResponse,
    ResourceFieldFilter,
    ResourceFieldMetadata,
    SavedSearch,
    SearchRequestTerm,
    SortSpec,
    TermSuggestion,
} from "@/arches_search/SimpleSearch/types.ts";

export async function createSearchMVTContext(params: {
    terms?: SearchRequestTerm[];
    query?: GroupPayload;
    graphSlugs?: string[];
    mapFilter?: FeatureCollection | null;
    dateRange?: DateRangeFilter | null;
    resourceFieldFilters?: ResourceFieldFilter[] | null;
}): Promise<{ context_id: string }> {
    const requestPayload = buildSearchApiRequestBody({
        terms: params.terms ?? [],
        query: params.query,
        graphSlugs: params.graphSlugs ?? [],
        mapFilter: params.mapFilter ?? null,
        dateRange: params.dateRange ?? null,
        resourceFieldFilters: params.resourceFieldFilters ?? null,
    });

    const url = generateArchesURL("arches_search:search_mvt_context");
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken") || "",
        },
        body: JSON.stringify(requestPayload),
    });
    if (!response.ok) {
        throw new Error(response.statusText);
    }
    return await response.json();
}

export async function fetchSearchResults({
    terms = [],
    query = {} as GroupPayload,
    graphSlugs = [],
    mapFilter = null,
    dateRange = null,
    resourceFieldFilters = null,
    page = 1,
    sort,
}: {
    terms?: SearchRequestTerm[];
    query?: GroupPayload;
    graphSlugs?: string[];
    mapFilter?: FeatureCollection | null;
    dateRange?: DateRangeFilter | null;
    resourceFieldFilters?: ResourceFieldFilter[] | null;
    page?: number;
    sort?: SortSpec[];
} = {}): Promise<SearchResults> {
    const requestPayload = buildSearchApiRequestBody({
        terms,
        query,
        graphSlugs,
        mapFilter,
        dateRange,
        resourceFieldFilters,
        page,
        sort,
    });

    const response = await fetch(generateArchesURL("arches_search:search"), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": Cookies.get("csrftoken") || "",
        },
        body: JSON.stringify(requestPayload),
    });

    if (!response.ok) {
        throw new Error(response.statusText);
    }

    return await response.json();
}

export async function fetchNodeFilterConfig(
    graphId: string,
    slug = "filtering",
): Promise<NodeFilterConfigResponse> {
    const response = await fetch(
        generateArchesURL(
            "arches_search:node_filter_config_for_graph",
            { graph_id: graphId },
            { slug },
        ),
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
        generateArchesURL(
            "arches_controlled_lists:controlled_list",
            { list_id: listId },
            { flat: "true" },
        ),
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
    const response = await fetch(
        generateArchesURL(
            "arches_search:term_suggestion_search",
            {},
            { q: query, lang: "*", flat: "true" },
        ),
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
    const queryParameters: Record<string, string> = { scope };
    if (search) {
        queryParameters.search = search;
    }
    const response = await fetch(
        generateArchesURL("arches_search:saved_searches", {}, queryParameters),
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
        generateArchesURL("arches_search:saved_search", { savedsearchid }),
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
    graphSlugs = [],
    dateRange = null,
    resourceFieldFilters = null,
    filename = "search_export",
    allDescriptors = false,
}: {
    terms?: SearchRequestTerm[];
    query?: GroupPayload;
    graphSlugs?: string[];
    dateRange?: DateRangeFilter | null;
    resourceFieldFilters?: ResourceFieldFilter[] | null;
    filename?: string;
    allDescriptors?: boolean;
}): Promise<void> {
    const requestPayload = buildSearchApiRequestBody({
        terms,
        query,
        graphSlugs,
        mapFilter: null,
        dateRange,
        resourceFieldFilters,
    });
    requestPayload.filename = filename;
    requestPayload.allDescriptors = allDescriptors;

    const response = await fetch(
        generateArchesURL("arches_search:search_export"),
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

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    window.URL.revokeObjectURL(url);
}

export async function fetchResourceFieldMetadata(
    graphSlugs: string[] = [],
): Promise<ResourceFieldMetadata[]> {
    const searchParams = new URLSearchParams();
    graphSlugs.forEach((graphSlug) =>
        searchParams.append("graph_slugs", graphSlug),
    );

    const url = `${generateArchesURL(
        "arches_search:resource_field_metadata",
    )}?${searchParams}`;
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(response.statusText);
    }

    const responseJson = await response.json();
    return responseJson.fields;
}
