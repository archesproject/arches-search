import NumericFilter from "@/arches_search/SimpleSearch/components/attribute-filters/NumericFilter.vue";
import ReferenceFilter from "@/arches_search/SimpleSearch/components/attribute-filters/ReferenceFilter.vue";

import {
    ClauseSubjectTypeToken,
    GraphScopeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";

import type {
    ClauseSubject,
    GroupPayload,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";
import type {
    AttributeFilterEntry,
    NumericFilterValue,
    ReferenceFilterValue,
} from "@/arches_search/SimpleSearch/components/attribute-filters/types.ts";

function nodeSubject(
    node: NodeFilterConfigNode,
    graphSlug: string,
): ClauseSubject {
    return {
        type: ClauseSubjectTypeToken.NODE,
        graph_slug: graphSlug,
        node_alias: node.node_alias,
        search_models: [],
    };
}

// Reference: a single REFERENCES_ANY clause whose operand is the list of
// selected labels. Matches the original hardcoded behavior in SimpleSearch.
function buildReferenceQuery(
    node: NodeFilterConfigNode,
    value: unknown,
    graphSlug: string,
): GroupPayload | null {
    const selected = (value as ReferenceFilterValue | null) ?? [];
    if (selected.length === 0) {
        return null;
    }

    return {
        graph_slug: graphSlug,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.AND,
        clauses: [
            {
                type: "LITERAL",
                quantifier: "ANY",
                subject: nodeSubject(node, graphSlug),
                operator: "REFERENCES_ANY",
                operands: [
                    {
                        type: "LITERAL",
                        value: selected.map((option) => option.label),
                    },
                ],
            },
        ],
        groups: [],
        aggregations: [],
        relationship: null,
    };
}

// Numeric: one clause per parsed token, OR-combined. A range becomes BETWEEN
// (arity 2); a discrete value becomes EQUALS.
function buildNumericQuery(
    node: NodeFilterConfigNode,
    value: unknown,
    graphSlug: string,
): GroupPayload | null {
    const tokens = (value as NumericFilterValue | null)?.tokens ?? [];
    if (tokens.length === 0) {
        return null;
    }

    const subject = nodeSubject(node, graphSlug);
    const clauses: LiteralClause[] = tokens.map((token) => {
        if (token.kind === "range") {
            return {
                type: "LITERAL",
                quantifier: "ANY",
                subject,
                operator: "BETWEEN",
                operands: [
                    { type: "LITERAL", value: token.min },
                    { type: "LITERAL", value: token.max },
                ],
            };
        }
        return {
            type: "LITERAL",
            quantifier: "ANY",
            subject,
            operator: "EQUALS",
            operands: [{ type: "LITERAL", value: token.value }],
        };
    });

    return {
        graph_slug: graphSlug,
        scope: GraphScopeToken.RESOURCE,
        logic: LogicToken.OR,
        clauses,
        groups: [],
        aggregations: [],
        relationship: null,
    };
}

function formatReferenceValue(value: unknown): string {
    const selected = (value as ReferenceFilterValue | null) ?? [];
    return selected.map((option) => option.label).join(", ");
}

function formatNumericValue(value: unknown): string {
    return (value as NumericFilterValue | null)?.text ?? "";
}

// Maps an Arches node datatype to its filter widget + query builder. Add a new
// datatype by registering one entry here and dropping in its widget component.
const ATTRIBUTE_FILTER_REGISTRY: Record<string, AttributeFilterEntry> = {
    reference: {
        component: ReferenceFilter,
        buildQuery: buildReferenceQuery,
        formatValue: formatReferenceValue,
    },
    number: {
        component: NumericFilter,
        buildQuery: buildNumericQuery,
        formatValue: formatNumericValue,
    },
};

export function getAttributeFilterEntry(
    datatype: string,
): AttributeFilterEntry | undefined {
    return ATTRIBUTE_FILTER_REGISTRY[datatype];
}

export function buildAttributeFilterQuery(
    node: NodeFilterConfigNode,
    value: unknown,
    graphSlug: string,
): GroupPayload | null {
    return (
        getAttributeFilterEntry(node.datatype)?.buildQuery(
            node,
            value,
            graphSlug,
        ) ?? null
    );
}

export function formatAttributeFilterValue(
    node: NodeFilterConfigNode,
    value: unknown,
): string {
    return getAttributeFilterEntry(node.datatype)?.formatValue(value) ?? "";
}
