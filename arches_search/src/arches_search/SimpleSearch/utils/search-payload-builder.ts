import {
    CLAUSE_TYPE_LITERAL,
    OPERAND_TYPE_GEO_LITERAL,
    OPERAND_TYPE_LITERAL,
    QUANTIFIER_ANY,
    SEARCH_MODELS_DATE,
    SEARCH_MODEL_GEOMETRY,
} from "@/arches_search/AdvancedSearch/types.ts";
import { SUGGESTION_DATATYPE_REFERENCE } from "@/arches_search/SimpleSearch/components/TermFilter/constants.ts";
import { TERM_KIND_CONTROLLED_TERM } from "@/arches_search/SimpleSearch/types.ts";

import type { FeatureCollection } from "geojson";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    DateRangeFilter,
    ResourceFieldFilter,
    SearchRequestTerm,
    SortSpec,
} from "@/arches_search/SimpleSearch/types.ts";

// The server lowers this to its own TERM_SEARCH_MAX_HOPS setting.
export const TERM_SEARCH_MAX_HOPS = 2;

// A string matches any datatype; an object only matches its own.
type TermSearchTerm = string | { text: string; datatype: string };

interface TermSearch {
    terms: TermSearchTerm[];
    max_hops: number;
}

interface ClauseOperand {
    type: typeof OPERAND_TYPE_LITERAL | typeof OPERAND_TYPE_GEO_LITERAL;
    value: unknown;
}

interface SearchClause {
    type: typeof CLAUSE_TYPE_LITERAL;
    quantifier: typeof QUANTIFIER_ANY;
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

function buildTermSearchTerm(term: SearchRequestTerm): TermSearchTerm {
    // A controlled term names a reference value, so it only matches those.
    if (term.type === TERM_KIND_CONTROLLED_TERM) {
        return { text: term.text, datatype: SUGGESTION_DATATYPE_REFERENCE };
    }
    return term.text;
}

function buildTermSearch(
    terms: SearchRequestTerm[],
    maxHops: number,
): TermSearch | null {
    if (terms.length === 0) {
        return null;
    }
    return {
        terms: terms.map(buildTermSearchTerm),
        max_hops: maxHops,
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
            type: CLAUSE_TYPE_LITERAL,
            quantifier: QUANTIFIER_ANY,
            subject: {
                type: "SEARCH_MODELS",
                graph_slug: graphSlug,
                node_alias: "",
                search_models: [SEARCH_MODEL_GEOMETRY],
            },
            operator: "GEO_INTERSECTS",
            operands: [{ type: OPERAND_TYPE_GEO_LITERAL, value: mapFilter }],
        });
    }

    if (dateRange) {
        // Both models, so a stored range overlapping the window qualifies and
        // not just a single date sitting inside it.
        clauses.push({
            type: CLAUSE_TYPE_LITERAL,
            quantifier: QUANTIFIER_ANY,
            subject: {
                type: "SEARCH_MODELS",
                graph_slug: graphSlug,
                node_alias: "",
                search_models: [...SEARCH_MODELS_DATE],
            },
            operator: "BETWEEN",
            operands: [
                { type: OPERAND_TYPE_LITERAL, value: dateRange.from },
                { type: OPERAND_TYPE_LITERAL, value: dateRange.to },
            ],
        });
    }

    return clauses;
}

function buildAdvancedSearchQueries(
    baseQueries: GroupPayload[],
    resourceFieldFilters: ResourceFieldFilter[] | null | undefined,
    mapFilter: FeatureCollection | null,
    dateRange: DateRangeFilter | null,
    graphSlugs: string[],
): Array<GroupPayload | Record<string, unknown>> | null {
    const resourceFieldClauses: SearchClause[] = (
        resourceFieldFilters ?? []
    ).map((filter) => ({
        type: CLAUSE_TYPE_LITERAL,
        quantifier: QUANTIFIER_ANY,
        subject: { type: "RESOURCE_FIELD", field: filter.field },
        operator: filter.operator,
        operands: (filter.operands ?? []).map((value) => ({
            type: OPERAND_TYPE_LITERAL,
            value,
        })),
    }));

    const hasClausesToPlace =
        resourceFieldClauses.length > 0 ||
        hasDrawnArea(mapFilter) ||
        Boolean(dateRange);

    if (!hasClausesToPlace) {
        return baseQueries.length > 0 ? baseQueries : null;
    }

    // A clause only filters the graph whose payload it sits in, so each is
    // repeated per resource model. The advanced query nests rather than merges,
    // so it stays AND-ed even when its own logic is OR.
    let targetSlugs = graphSlugs;
    if (targetSlugs.length === 0) {
        targetSlugs = baseQueries.map((baseQuery) => baseQuery.graph_slug);
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
        groups: baseQueries.filter(
            (baseQuery) => baseQuery.graph_slug === graphSlug,
        ),
        aggregations: [],
        relationship: null,
    }));
}

export function buildSearchApiRequestBody({
    terms,
    query,
    queries,
    graphSlugs,
    mapFilter,
    dateRange,
    resourceFieldFilters,
    maxHops = TERM_SEARCH_MAX_HOPS,
    page,
    sort,
}: {
    terms: SearchRequestTerm[];
    // One query for one graph; `queries` takes one per graph.
    query?: GroupPayload;
    queries?: GroupPayload[];
    graphSlugs: string[];
    mapFilter: FeatureCollection | null;
    dateRange?: DateRangeFilter | null;
    resourceFieldFilters?: ResourceFieldFilter[] | null;
    maxHops?: number;
    page?: number;
    sort?: SortSpec[];
}): Record<string, unknown> {
    let baseQueries: GroupPayload[] = queries ?? [];
    if (!queries && query) {
        baseQueries = [query];
    }

    const requestPayload: Record<string, unknown> = {
        graph_slugs: graphSlugs.length > 0 ? graphSlugs : null,
        term_search: buildTermSearch(terms, maxHops),
        advanced_search_queries: buildAdvancedSearchQueries(
            baseQueries,
            resourceFieldFilters,
            mapFilter,
            dateRange ?? null,
            graphSlugs,
        ),
    };

    if (page !== undefined) {
        requestPayload.pagination = { page };
    }
    if (sort !== undefined) {
        requestPayload.sort = sort;
    }

    return requestPayload;
}
