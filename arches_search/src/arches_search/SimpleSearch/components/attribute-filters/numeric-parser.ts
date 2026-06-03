import type { NumericToken } from "@/arches_search/SimpleSearch/components/attribute-filters/types.ts";

// Describes why a numeric expression failed to parse. The component maps each
// code to a localized message; keeping codes here keeps the parser pure and
// testable without a translation layer.
export type NumericParseError =
    | { code: "INVALID_TOKEN"; token: string }
    | { code: "MALFORMED_RANGE"; token: string }
    | { code: "RANGE_ORDER"; token: string };

export interface NumericParseResult {
    tokens: NumericToken[];
    error: NumericParseError | null;
}

// Non-negative integer or decimal. Negatives and open-ended ranges are
// intentionally rejected so that "-" is unambiguously the range separator.
const NUMBER_PATTERN = /^\d+(\.\d+)?$/;

const RANGE_SEPARATOR = "-";
const TOKEN_SEPARATOR = ",";

// Parses a printer-pagination-style expression such as "9-10, 12, 15.5" into
// tokens. Comma-separated segments are OR-combined by the query builder. A
// segment is either a single value (-> EQUALS) or a low-high range (-> BETWEEN).
// Whitespace and empty segments (e.g. trailing commas) are ignored. The first
// malformed segment short-circuits with an error and no tokens, so callers can
// block applying a partially-valid filter.
export function parseNumericFilter(text: string): NumericParseResult {
    const segments = text
        .split(TOKEN_SEPARATOR)
        .map((segment) => segment.trim())
        .filter((segment) => segment.length > 0);

    const tokens: NumericToken[] = [];

    for (const segment of segments) {
        const result = parseSegment(segment);
        if (result.error) {
            return { tokens: [], error: result.error };
        }
        tokens.push(result.token);
    }

    return { tokens, error: null };
}

function parseSegment(
    segment: string,
):
    | { token: NumericToken; error: null }
    | { token: null; error: NumericParseError } {
    if (segment.includes(RANGE_SEPARATOR)) {
        const parts = segment.split(RANGE_SEPARATOR);
        if (parts.length !== 2 || !isNumber(parts[0]) || !isNumber(parts[1])) {
            return {
                token: null,
                error: { code: "MALFORMED_RANGE", token: segment },
            };
        }
        const min = Number(parts[0]);
        const max = Number(parts[1]);
        if (min > max) {
            return {
                token: null,
                error: { code: "RANGE_ORDER", token: segment },
            };
        }
        return { token: { kind: "range", min, max }, error: null };
    }

    if (!isNumber(segment)) {
        return {
            token: null,
            error: { code: "INVALID_TOKEN", token: segment },
        };
    }

    return { token: { kind: "value", value: Number(segment) }, error: null };
}

function isNumber(candidate: string): boolean {
    return NUMBER_PATTERN.test(candidate);
}
