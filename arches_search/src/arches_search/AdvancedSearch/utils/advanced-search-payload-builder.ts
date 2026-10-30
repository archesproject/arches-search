import dayjs from "dayjs";

import {
    type LiteralClause,
    type LiteralOperand,
    ClauseSubjectTypeToken,
} from "@/arches_search/AdvancedSearch/types.ts";

const CLAUSE_TYPE_LITERAL = "LITERAL";
const QUANTIFIER_ANY = "ANY";
const SEARCH_MODELS_DATE = ["DateSearch", "DateRangeSearch"] as const;

export function parseStoredDate(value: unknown): Date | null {
    if (!value) return null;
    const parsed = dayjs(String(value));
    return parsed.isValid() ? parsed.toDate() : null;
}

export function buildNodeDateSearchClause(
    graphSlug: string,
    nodeAlias: string,
    operator: string,
    dateFrom: string,
    dateTo?: string,
): LiteralClause {
    const operands: LiteralOperand[] = [
        { type: CLAUSE_TYPE_LITERAL, value: dateFrom },
    ];
    if (dateTo) operands.push({ type: CLAUSE_TYPE_LITERAL, value: dateTo });
    return {
        type: CLAUSE_TYPE_LITERAL,
        quantifier: QUANTIFIER_ANY,
        subject: {
            type: ClauseSubjectTypeToken.NODE,
            graph_slug: graphSlug,
            node_alias: nodeAlias,
            search_models: [],
        },
        operator,
        operands,
    };
}

export function buildDateSearchClause(
    graphSlug: string,
    operator: string,
    dateFrom: string,
    dateTo?: string,
): LiteralClause {
    const operands: LiteralOperand[] = [
        { type: CLAUSE_TYPE_LITERAL, value: dateFrom },
    ];
    if (dateTo) operands.push({ type: CLAUSE_TYPE_LITERAL, value: dateTo });
    return {
        type: CLAUSE_TYPE_LITERAL,
        quantifier: QUANTIFIER_ANY,
        subject: {
            type: ClauseSubjectTypeToken.SEARCH_MODELS,
            graph_slug: graphSlug,
            node_alias: "",
            search_models: [...SEARCH_MODELS_DATE],
        },
        operator,
        operands,
    };
}
