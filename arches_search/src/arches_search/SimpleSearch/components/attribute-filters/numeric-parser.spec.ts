import { describe, expect, it } from "vitest";

import { parseNumericFilter } from "@/arches_search/SimpleSearch/components/attribute-filters/numeric-parser.ts";

describe("parseNumericFilter", () => {
    it("treats empty input as a cleared filter", () => {
        expect(parseNumericFilter("")).toEqual({ tokens: [], error: null });
        expect(parseNumericFilter("   ")).toEqual({ tokens: [], error: null });
    });

    it("parses a single value", () => {
        expect(parseNumericFilter("12")).toEqual({
            tokens: [{ kind: "value", value: 12 }],
            error: null,
        });
    });

    it("parses a closed range", () => {
        expect(parseNumericFilter("9-10")).toEqual({
            tokens: [{ kind: "range", min: 9, max: 10 }],
            error: null,
        });
    });

    it("parses decimals", () => {
        expect(parseNumericFilter("15.5")).toEqual({
            tokens: [{ kind: "value", value: 15.5 }],
            error: null,
        });
    });

    it("parses a mix of ranges and values, ignoring whitespace", () => {
        expect(parseNumericFilter("9-10, 12 , 15.5")).toEqual({
            tokens: [
                { kind: "range", min: 9, max: 10 },
                { kind: "value", value: 12 },
                { kind: "value", value: 15.5 },
            ],
            error: null,
        });
    });

    it("ignores empty segments from extra or trailing commas", () => {
        expect(parseNumericFilter("9-10, , 12,")).toEqual({
            tokens: [
                { kind: "range", min: 9, max: 10 },
                { kind: "value", value: 12 },
            ],
            error: null,
        });
    });

    it("accepts an equal-bound range", () => {
        expect(parseNumericFilter("5-5")).toEqual({
            tokens: [{ kind: "range", min: 5, max: 5 }],
            error: null,
        });
    });

    it("rejects a reversed range", () => {
        const result = parseNumericFilter("10-9");
        expect(result.tokens).toEqual([]);
        expect(result.error).toEqual({ code: "RANGE_ORDER", token: "10-9" });
    });

    it("rejects non-numeric tokens", () => {
        const result = parseNumericFilter("9-10, abc");
        expect(result.tokens).toEqual([]);
        expect(result.error).toEqual({ code: "INVALID_TOKEN", token: "abc" });
    });

    it("rejects open-ended and negative ranges", () => {
        expect(parseNumericFilter("9-").error).toEqual({
            code: "MALFORMED_RANGE",
            token: "9-",
        });
        expect(parseNumericFilter("-10").error).toEqual({
            code: "MALFORMED_RANGE",
            token: "-10",
        });
    });

    it("rejects malformed ranges with too many bounds", () => {
        expect(parseNumericFilter("1-2-3").error).toEqual({
            code: "MALFORMED_RANGE",
            token: "1-2-3",
        });
    });
});
