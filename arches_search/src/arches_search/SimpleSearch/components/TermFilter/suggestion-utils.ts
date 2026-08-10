import {
    TERM_KIND_CONTROLLED_TERM,
    TERM_KIND_RECORD,
} from "@/arches_search/SimpleSearch/types.ts";
import type {
    TermKind,
    TermSuggestion,
} from "@/arches_search/SimpleSearch/types.ts";

const SUGGESTION_DATATYPE_REFERENCE = "reference";
export const SUGGESTION_DATATYPE_STRING = "string";

interface HighlightSegment {
    text: string;
    matched: boolean;
}

interface TermSuggestionAdditionalInfo {
    path?: unknown;
}

export function isConceptSuggestion(suggestion: TermSuggestion): boolean {
    return suggestion.datatype === SUGGESTION_DATATYPE_REFERENCE;
}

export function getTermKind(suggestion: TermSuggestion): TermKind | undefined {
    if (isConceptSuggestion(suggestion)) {
        return TERM_KIND_CONTROLLED_TERM;
    }
    if (suggestion.resourceinstanceid) {
        return TERM_KIND_RECORD;
    }
    return undefined;
}

function escapeRegExp(value: string): string {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function getHighlightSegments(
    text: string,
    query: string,
): HighlightSegment[] {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
        return [{ text, matched: false }];
    }

    const matchPattern = new RegExp(`(${escapeRegExp(trimmedQuery)})`, "gi");
    return text
        .split(matchPattern)
        .map((segment, index) => ({ text: segment, matched: index % 2 === 1 }))
        .filter((segment) => segment.text !== "");
}

export function getSuggestionPath(suggestion: TermSuggestion): string | null {
    const additionalInfo = suggestion.addtional_info as
        | TermSuggestionAdditionalInfo
        | undefined;
    const suggestionPath = additionalInfo?.path;

    if (
        !Array.isArray(suggestionPath) ||
        suggestionPath.length === 0 ||
        !suggestionPath.every((pathItem) => typeof pathItem === "string")
    ) {
        return null;
    }

    return suggestionPath.join(" > ");
}
