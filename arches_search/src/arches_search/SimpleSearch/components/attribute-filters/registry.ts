import NumericFilter from "@/arches_search/SimpleSearch/components/attribute-filters/NumericFilter.vue";
import ReferenceFilterMultiSelect from "@/arches_search/SimpleSearch/components/attribute-filters/ReferenceFilterMultiSelect.vue";

import {
    CLAUSE_TYPE_LITERAL,
    ClauseSubjectTypeToken,
    GraphScopeToken,
    LogicToken,
    OPERAND_TYPE_LITERAL,
    QUANTIFIER_ANY,
} from "@/arches_search/AdvancedSearch/types.ts";
import {
    isLabelList,
    isReferenceValueList,
    referenceValueLabel,
} from "@/arches_search/AdvancedSearch/utils/reference-labels.ts";

import type {
    ClauseSubject,
    GroupPayload,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";
import type {
    AttributeFilterEntry,
    NumericFilterValue,
    NumericToken,
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

// Reference: a single REFERENCES_ANY clause whose operand is the list items
// selected.
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
                type: CLAUSE_TYPE_LITERAL,
                quantifier: QUANTIFIER_ANY,
                subject: nodeSubject(node, graphSlug),
                operator: "REFERENCES_ANY",
                operands: [
                    {
                        type: OPERAND_TYPE_LITERAL,
                        value: selected,
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
                type: CLAUSE_TYPE_LITERAL,
                quantifier: QUANTIFIER_ANY,
                subject,
                operator: "BETWEEN",
                operands: [
                    { type: OPERAND_TYPE_LITERAL, value: token.min },
                    { type: OPERAND_TYPE_LITERAL, value: token.max },
                ],
            };
        }
        return {
            type: CLAUSE_TYPE_LITERAL,
            quantifier: QUANTIFIER_ANY,
            subject,
            operator: "EQUALS",
            operands: [{ type: OPERAND_TYPE_LITERAL, value: token.value }],
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
    if (isLabelList(selected)) {
        return selected.join(", ");
    }
    return selected.map(referenceValueLabel).join(", ");
}

function formatNumericValue(value: unknown): string {
    return (value as NumericFilterValue | null)?.text ?? "";
}

function parseReferenceValue(query: GroupPayload): ReferenceFilterValue {
    const value = query.clauses[0]?.operands[0]?.value;
    if (isLabelList(value) || isReferenceValueList(value)) {
        return value;
    }
    return [];
}

function parseNumericValue(query: GroupPayload): NumericFilterValue {
    const tokens = query.clauses.flatMap((clause): NumericToken[] => {
        const [first, second] = clause.operands.map((operand) => operand.value);
        if (clause.operator === "BETWEEN") {
            return [{ kind: "range", min: Number(first), max: Number(second) }];
        }
        if (clause.operator === "EQUALS") {
            return [{ kind: "value", value: Number(first) }];
        }
        return [];
    });

    const text = tokens
        .map((token) => {
            if (token.kind === "range") {
                return `${token.min}-${token.max}`;
            }
            return String(token.value);
        })
        .join(", ");

    return { text, tokens };
}

// Maps an Arches node datatype to its filter widget + query builder. Add a new
// datatype by registering one entry here and dropping in its widget component.
const ATTRIBUTE_FILTER_REGISTRY: Record<string, AttributeFilterEntry> = {
    reference: {
        component: ReferenceFilterMultiSelect,
        buildQuery: buildReferenceQuery,
        formatValue: formatReferenceValue,
        parseValue: parseReferenceValue,
    },
    number: {
        component: NumericFilter,
        buildQuery: buildNumericQuery,
        formatValue: formatNumericValue,
        parseValue: parseNumericValue,
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

export function parseAttributeFilterValue(
    node: NodeFilterConfigNode,
    query: GroupPayload,
): unknown {
    return getAttributeFilterEntry(node.datatype)?.parseValue(query) ?? null;
}
