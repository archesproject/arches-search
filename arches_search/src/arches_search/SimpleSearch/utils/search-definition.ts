import { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";
import {
    TERM_KIND_CONTROLLED_TERM,
    TERM_KIND_RECORD,
} from "@/arches_search/SimpleSearch/types.ts";

import type { FeatureCollection } from "geojson";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    SearchDefinition,
    SerializedTerm,
    TermKind,
} from "@/arches_search/SimpleSearch/types.ts";

export interface SearchRequestTerm {
    type: "string" | typeof TERM_KIND_CONTROLLED_TERM;
    text: string;
    inverted: boolean;
}

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

export function buildRequestQuery(
    queries: GroupPayload[],
): GroupPayload | undefined {
    if (queries.length === 0) {
        return undefined;
    }
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

    let graphIds: string[] = [];
    if (Array.isArray(raw.graphIds)) {
        graphIds = raw.graphIds.filter(
            (id): id is string => typeof id === "string",
        );
    }

    let mapFilter: FeatureCollection | null = null;
    if (raw.mapFilter && typeof raw.mapFilter === "object") {
        mapFilter = raw.mapFilter as FeatureCollection;
    }

    return { terms, queries: queriesIn, graphIds, mapFilter };
}
