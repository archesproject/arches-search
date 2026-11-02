import {
    CLAUSE_TYPE_LITERAL,
    ClauseSubjectTypeToken,
    OPERAND_TYPE_LITERAL,
    QUANTIFIER_ANY,
    SEARCH_MODELS_DATE,
} from "@/arches_search/AdvancedSearch/types.ts";

import type {
    ClauseSubject,
    LiteralClause,
} from "@/arches_search/AdvancedSearch/types.ts";

const OPERATOR_BETWEEN = "BETWEEN";

// Without a node alias the clause matches any date in the model.
export function buildTimeFilterClause(
    graphSlug: string,
    nodeAlias: string | null,
    dateFrom: string,
    dateTo: string,
): LiteralClause {
    let subject: ClauseSubject = {
        type: ClauseSubjectTypeToken.SEARCH_MODELS,
        graph_slug: graphSlug,
        node_alias: "",
        search_models: [...SEARCH_MODELS_DATE],
    };
    if (nodeAlias) {
        subject = {
            type: ClauseSubjectTypeToken.NODE,
            graph_slug: graphSlug,
            node_alias: nodeAlias,
            search_models: [],
        };
    }
    return {
        type: CLAUSE_TYPE_LITERAL,
        quantifier: QUANTIFIER_ANY,
        subject,
        operator: OPERATOR_BETWEEN,
        operands: [
            { type: OPERAND_TYPE_LITERAL, value: dateFrom },
            { type: OPERAND_TYPE_LITERAL, value: dateTo },
        ],
    };
}
