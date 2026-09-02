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
    ResourceFieldFilter,
    ResourceFieldMetadata,
} from "@/arches_search/SimpleSearch/types.ts";
import type { FeatureCollection } from "geojson";

interface SearchRequestTerm {
    type: string;
    text: string;
    inverted: boolean;
}

interface DateRangeFilter {
    from: string;
    to: string;
}

interface NodeAgnosticFilter {
    type: "TEXT_MATCH" | "GEO_INTERSECTS" | "DATE_RANGE";
    value: string[] | FeatureCollection | DateRangeFilter;
    max_hops: number;
}

function buildNodeAgnosticFilters(
    terms: SearchRequestTerm[],
    mapFilter: FeatureCollection | null,
    dateRange: DateRangeFilter | null,
): NodeAgnosticFilter[] | null {
    const filters: NodeAgnosticFilter[] = [];

    if (terms.length > 0) {
        filters.push({
            type: "TEXT_MATCH",
            value: terms.map((term) => term.text),
            max_hops: 2,
        });
    }

    if (mapFilter && mapFilter.features && mapFilter.features.length > 0) {
        filters.push({ type: "GEO_INTERSECTS", value: mapFilter, max_hops: 0 });
    }

    if (dateRange) {
        filters.push({ type: "DATE_RANGE", value: dateRange, max_hops: 0 });
    }

    return filters.length > 0 ? filters : null;
}

function buildSearchApiRequestBody({
    terms,
    query,
    graphIds,
    mapFilter,
    dateRange,
    resourceFieldFilters,
    page,
    sort,
}: {
    terms: SearchRequestTerm[];
    query?: GroupPayload;
    graphIds: string[];
    mapFilter: FeatureCollection | null;
    dateRange?: DateRangeFilter | null;
    resourceFieldFilters?: ResourceFieldFilter[] | null;
    page?: number;
    sort?: SortSpec[];
}): Record<string, unknown> {
    const requestPayload: Record<string, unknown> = {
        graph_ids: graphIds.length > 0 ? graphIds : null,
        node_agnostic_filters: buildNodeAgnosticFilters(
            terms,
            mapFilter,
            dateRange ?? null,
        ),
        advanced_search_query:
            query && Object.keys(query).length > 0 ? query : null,
        resource_field_filters:
            resourceFieldFilters && resourceFieldFilters.length > 0
                ? resourceFieldFilters
                : null,
    };

    if (page !== undefined) {
        requestPayload.page = page;
    }
    if (sort !== undefined) {
        requestPayload.sort = sort;
    }

    return requestPayload;
}

export async function createSearchMVTContext(params: {
    terms?: SearchRequestTerm[];
    query?: GroupPayload;
    graphIds?: string[];
    mapFilter?: FeatureCollection | null;
    dateRange?: DateRangeFilter | null;
}): Promise<{ context_id: string }> {
    const requestPayload = buildSearchApiRequestBody({
        terms: params.terms ?? [],
        query: params.query,
        graphIds: params.graphIds ?? [],
        mapFilter: params.mapFilter ?? null,
        dateRange: params.dateRange ?? null,
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
    graphIds = [],
    mapFilter = null,
    dateRange = null,
    resourceFieldFilters = null,
    page = 1,
    sort,
}: {
    terms?: SearchRequestTerm[];
    query?: GroupPayload;
    graphIds?: string[];
    mapFilter?: FeatureCollection | null;
    dateRange?: DateRangeFilter | null;
    resourceFieldFilters?: ResourceFieldFilter[] | null;
    page?: number;
    sort?: SortSpec[];
} = {}): Promise<SearchResults> {
    const requestPayload = buildSearchApiRequestBody({
        terms,
        query,
        graphIds,
        mapFilter,
        dateRange,
        resourceFieldFilters,
        page,
        sort,
    });

    const response = await fetch(
        `${generateArchesURL("arches_search:search")}`,
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
    dateRange = null,
    filename = "search_export",
    allDescriptors = false,
}: {
    terms?: SearchRequestTerm[];
    query?: GroupPayload;
    graphIds?: string[];
    dateRange?: DateRangeFilter | null;
    filename?: string;
    allDescriptors?: boolean;
}): Promise<void> {
    const requestPayload = buildSearchApiRequestBody({
        terms,
        query,
        graphIds,
        mapFilter: null,
        dateRange,
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
    graphIds: string[] = [],
): Promise<ResourceFieldMetadata[]> {
    const searchParams = new URLSearchParams();
    graphIds.forEach((graphId) => searchParams.append("graph_ids", graphId));

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
