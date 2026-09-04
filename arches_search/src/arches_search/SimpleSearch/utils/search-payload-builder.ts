import type { FeatureCollection } from "geojson";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    DateRangeFilter,
    ResourceFieldFilter,
    SearchRequestTerm,
    SortSpec,
} from "@/arches_search/SimpleSearch/types.ts";

const TERM_SEARCH_MAX_HOPS = 2;

interface TermSearch {
    terms: string[];
    max_hops: number;
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
        operands: (filter.operands ?? []).map((value) => ({
            type: "LITERAL",
            value,
        })),
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
    let targetSlugs = graphSlugs;
    if (targetSlugs.length === 0 && baseQuery) {
        targetSlugs = [baseQuery.graph_slug];
    }
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

export function buildSearchApiRequestBody({
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
