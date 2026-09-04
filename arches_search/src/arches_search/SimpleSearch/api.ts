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

interface TermSearch {
    terms: string[];
    max_hops: number;
}

// Matched anywhere, then walked across relationships.
const TERM_SEARCH_MAX_HOPS = 2;

function buildTermSearch(terms: SearchRequestTerm[]): TermSearch | null {
    if (terms.length === 0) {
        return null;
    }
    return {
        terms: terms.map((term) => term.text),
        max_hops: TERM_SEARCH_MAX_HOPS,
    };
}

function hasDrawnArea(mapFilter: FeatureCollection | null): boolean {
    return Boolean(
        mapFilter && mapFilter.features && mapFilter.features.length,
    );
}

function buildSearchModelClauses(
    graphSlug: string,
    mapFilter: FeatureCollection | null,
    dateRange: DateRangeFilter | null,
): SearchClause[] {
    const clauses: SearchClause[] = [];

    if (hasDrawnArea(mapFilter)) {
        clauses.push({
            type: "LITERAL",
            quantifier: "ANY",
            subject: {
                type: "SEARCH_MODELS",
                graph_slug: graphSlug,
                node_alias: "",
                search_models: ["GeometrySearch"],
            },
            operator: "GEO_INTERSECTS",
            operands: [{ type: "GEO_LITERAL", value: mapFilter }],
        });
    }

    if (dateRange) {
        // Both models, so a stored range overlapping the window qualifies and
        // not just a single date sitting inside it.
        clauses.push({
            type: "LITERAL",
            quantifier: "ANY",
            subject: {
                type: "SEARCH_MODELS",
                graph_slug: graphSlug,
                node_alias: "",
                search_models: ["DateSearch", "DateRangeSearch"],
            },
            operator: "BETWEEN",
            operands: [
                { type: "LITERAL", value: dateRange.from },
                { type: "LITERAL", value: dateRange.to },
            ],
        });
    }

    return clauses;
}

interface ClauseOperand {
    type: "LITERAL" | "GEO_LITERAL";
    value: unknown;
}

interface SearchClause {
    type: "LITERAL";
    quantifier: "ANY";
    subject:
        | { type: "RESOURCE_FIELD"; field: string }
        | {
              type: "SEARCH_MODELS";
              graph_slug: string;
              node_alias: "";
              search_models: string[];
          };
    operator: string;
    operands: ClauseOperand[];
}

function isRangeValue(value: unknown): value is { from: unknown; to: unknown } {
    return (
        typeof value === "object" &&
        value !== null &&
        !Array.isArray(value) &&
        "from" in value &&
        "to" in value
    );
}

function buildResourceFieldOperands(value: unknown): ClauseOperand[] {
    // Mirrors the facet rows' param_formats: no value means no operand, a
    // from/to pair is two, anything else is one.
    if (value === undefined || value === null) {
        return [];
    }
    if (isRangeValue(value)) {
        return [
            { type: "LITERAL", value: value.from },
            { type: "LITERAL", value: value.to },
        ];
    }
    return [{ type: "LITERAL", value }];
}

function buildAdvancedSearchQueries(
    query: GroupPayload | undefined,
    resourceFieldFilters: ResourceFieldFilter[] | null | undefined,
    mapFilter: FeatureCollection | null,
    dateRange: DateRangeFilter | null,
    graphSlugs: string[],
): Array<GroupPayload | Record<string, unknown>> | null {
    const baseQuery = query && Object.keys(query).length > 0 ? query : null;
    const resourceFieldClauses: SearchClause[] = (
        resourceFieldFilters ?? []
    ).map((filter) => ({
        type: "LITERAL",
        quantifier: "ANY",
        subject: { type: "RESOURCE_FIELD", field: filter.field },
        operator: filter.operator,
        operands: buildResourceFieldOperands(filter.value),
    }));

    const hasClausesToPlace =
        resourceFieldClauses.length > 0 ||
        hasDrawnArea(mapFilter) ||
        Boolean(dateRange);

    if (!hasClausesToPlace) {
        return baseQuery ? [baseQuery] : null;
    }

    // A clause only filters the graph whose payload it sits in, so each is
    // repeated per resource model. The advanced query nests rather than merges,
    // so it stays AND-ed even when its own logic is OR.
    const targetSlugs =
        graphSlugs.length > 0
            ? graphSlugs
            : baseQuery
              ? [baseQuery.graph_slug]
              : [];

    if (targetSlugs.length === 0) {
        return null;
    }

    return targetSlugs.map((graphSlug) => ({
        graph_slug: graphSlug,
        scope: "RESOURCE",
        logic: "AND",
        clauses: [
            ...resourceFieldClauses,
            ...buildSearchModelClauses(graphSlug, mapFilter, dateRange),
        ],
        groups:
            baseQuery && baseQuery.graph_slug === graphSlug ? [baseQuery] : [],
        aggregations: [],
        relationship: null,
    }));
}

function buildSearchApiRequestBody({
    terms,
    query,
    graphSlugs,
    mapFilter,
    dateRange,
    resourceFieldFilters,
    page,
    sort,
}: {
    terms: SearchRequestTerm[];
    query?: GroupPayload;
    graphSlugs: string[];
    mapFilter: FeatureCollection | null;
    dateRange?: DateRangeFilter | null;
    resourceFieldFilters?: ResourceFieldFilter[] | null;
    page?: number;
    sort?: SortSpec[];
}): Record<string, unknown> {
    const requestPayload: Record<string, unknown> = {
        graph_slugs: graphSlugs.length > 0 ? graphSlugs : null,
        term_search: buildTermSearch(terms),
        advanced_search_queries: buildAdvancedSearchQueries(
            query,
            resourceFieldFilters,
            mapFilter,
            dateRange ?? null,
            graphSlugs,
        ),
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
