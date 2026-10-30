import {
    ClauseSubjectTypeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    ADVANCED_QUERY_KEY,
    TERM_KIND_CONTROLLED_TERM,
    TERM_KIND_RECORD,
} from "@/arches_search/SimpleSearch/types.ts";

import type { FeatureCollection } from "geojson";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    DateRangeFilter,
    SearchDefinition,
    SearchRequestTerm,
    SerializedTerm,
    SortSpec,
    TermKind,
} from "@/arches_search/SimpleSearch/types.ts";

export function isTermKind(value: unknown): value is TermKind {
    return value === TERM_KIND_CONTROLLED_TERM || value === TERM_KIND_RECORD;
}

export function buildRequestTerms(
    terms: { text: string; inverted: boolean; termKind?: TermKind }[],
): SearchRequestTerm[] {
    return terms.map((term) => {
        let type: SearchRequestTerm["type"] = "string";
        if (term.termKind === TERM_KIND_CONTROLLED_TERM) {
            type = term.termKind;
        }
        return { type, text: term.text, inverted: term.inverted };
    });
}

// The "all date nodes" time filter is stored as a single SEARCH_MODELS clause
// on one graph, but is sent as a date range that filters every searched graph
// rather than as part of the query — see buildRequestDateRange.
function isNodeAgnosticDateQuery(payload: GroupPayload): boolean {
    return (
        payload.clauses.length === 1 &&
        payload.clauses[0].subject.type === ClauseSubjectTypeToken.SEARCH_MODELS
    );
}

export function buildRequestDateRange(
    queries: GroupPayload[],
): DateRangeFilter | null {
    const dateQuery = queries.find(isNodeAgnosticDateQuery);
    if (!dateQuery) {
        return null;
    }
    const [fromOperand, toOperand] = dateQuery.clauses[0].operands;
    return {
        from: fromOperand.value as string,
        to:
            (toOperand?.value as string | undefined) ??
            (fromOperand.value as string),
    };
}

export function buildRequestQuery(
    queries: GroupPayload[],
): GroupPayload | undefined {
    const advancedQueries = queries.filter(
        (payload) => !isNodeAgnosticDateQuery(payload),
    );
    if (advancedQueries.length === 0) {
        return undefined;
    }
    return mergeQueries(advancedQueries);
}

// The API takes one payload per graph, so queries are grouped by the graph
// they filter and each group is AND-combined. A query for a graph that is not
// being searched is left out rather than sent to be ignored.
export function buildRequestQueries(
    queries: GroupPayload[],
    requestedGraphSlugs: string[],
): GroupPayload[] {
    const requestedGraphSlugSet = new Set(requestedGraphSlugs);
    const queriesByGraphSlug = new Map<string, GroupPayload[]>();

    for (const payload of queries) {
        if (
            isNodeAgnosticDateQuery(payload) ||
            !requestedGraphSlugSet.has(payload.graph_slug)
        ) {
            continue;
        }
        queriesByGraphSlug.set(payload.graph_slug, [
            ...(queriesByGraphSlug.get(payload.graph_slug) ?? []),
            payload,
        ]);
    }

    return [...queriesByGraphSlug.values()].map(mergeQueries);
}

function mergeQueries(queries: GroupPayload[]): GroupPayload {
    if (queries.length === 1) {
        return queries[0];
    }
    return {
        graph_slug: queries[0].graph_slug,
        scope: queries[0].scope,
        logic: LogicToken.AND,
        clauses: [],
        groups: queries,
        aggregations: [],
        relationship: null,
    };
}

export function parseSearchDefinition(
    raw: Record<string, unknown>,
): SearchDefinition {
    const rawTerms = Array.isArray(raw.terms) ? raw.terms : [];
    const terms = rawTerms.flatMap((rawTerm) => {
        if (!rawTerm || typeof rawTerm !== "object") {
            return [];
        }
        const term = rawTerm as Record<string, unknown>;
        const id = typeof term.id === "string" ? term.id : null;
        const text = typeof term.text === "string" ? term.text : null;
        if (!id || text === null) {
            return [];
        }

        const parsedTerm: SerializedTerm = {
            id,
            text,
            inverted: term.inverted === true,
        };
        if (isTermKind(term.termKind)) {
            parsedTerm.termKind = term.termKind;
        }
        if (typeof term.icon === "string") {
            parsedTerm.icon = term.icon;
        }
        if (term.options && typeof term.options === "object") {
            parsedTerm.options = term.options as Record<string, unknown>;
        }

        return [parsedTerm];
    });

    let queriesIn: SearchDefinition["queries"] = {};
    if (raw.queries && typeof raw.queries === "object") {
        queriesIn = raw.queries as SearchDefinition["queries"];
    }

    let graphSlugs: string[] = [];
    if (Array.isArray(raw.graphSlugs)) {
        graphSlugs = raw.graphSlugs.filter(
            (slug): slug is string => typeof slug === "string",
        );
    }

    let mapFilter: FeatureCollection | null = null;
    if (raw.mapFilter && typeof raw.mapFilter === "object") {
        mapFilter = raw.mapFilter as FeatureCollection;
    }

    let sort: SortSpec[] = [];
    if (Array.isArray(raw.sort)) {
        sort = raw.sort.filter(isSortSpec);
    }

    return { terms, queries: queriesIn, graphSlugs, mapFilter, sort };
}

function isSortSpec(value: unknown): value is SortSpec {
    return (
        typeof value === "object" &&
        value !== null &&
        typeof (value as Record<string, unknown>).type === "string" &&
        typeof (value as Record<string, unknown>).direction === "string"
    );
}

// What Advanced Search saves: its query alone, on its model.
export function buildAdvancedSearchDefinition(
    graphSlug: string,
    advancedQuery: GroupPayload | null,
    sort: SortSpec[],
): SearchDefinition {
    let queries: Record<string, GroupPayload> = {};
    if (advancedQuery) {
        queries = { [ADVANCED_QUERY_KEY]: advancedQuery };
    }
    return {
        terms: [],
        queries,
        graphSlugs: [graphSlug],
        mapFilter: null,
        sort,
    };
}
