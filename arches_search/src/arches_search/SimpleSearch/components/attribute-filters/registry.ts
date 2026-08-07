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
    value: ReferenceFilterValue | null,
    graphSlug: string,
): GroupPayload | null {
    const selected = value ?? [];
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
    value: NumericFilterValue | null,
    graphSlug: string,
): GroupPayload | null {
    const tokens = value?.tokens ?? [];
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

function formatReferenceValue(value: ReferenceFilterValue | null): string {
    const selected = value ?? [];
    return selected.map((option) => option.label).join(", ");
}

function formatNumericValue(value: NumericFilterValue | null): string {
    return value?.text ?? "";
}

// Maps an Arches node datatype to its filter widget + query builder. Add a new
// datatype by registering one entry here and dropping in its widget component.
// The value type is only known per-entry (it's whatever that entry's own
// component emits), so callers reach it through `unknown` at the two exported
// functions below rather than every builder/formatter re-asserting it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- heterogeneous registry: each entry's real value type differs and is only known by construction
const ATTRIBUTE_FILTER_REGISTRY: Record<string, AttributeFilterEntry<any>> = {
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
): AttributeFilterEntry<unknown> | undefined {
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
