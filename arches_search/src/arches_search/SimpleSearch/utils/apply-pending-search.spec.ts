import { describe, expect, it, vi } from "vitest";

import { applyPendingSearch } from "@/arches_search/SimpleSearch/utils/apply-pending-search.ts";
import {
    TERM_FILTER_KEY,
    TERM_KIND_RECORD,
} from "@/arches_search/SimpleSearch/types.ts";

import type { PendingSearchActions } from "@/arches_search/SimpleSearch/utils/apply-pending-search.ts";

function buildActions(): PendingSearchActions {
    return {
        applySearchDefinition: vi.fn(),
        clearAll: vi.fn(),
        openMapFilter: vi.fn(),
        setGraphsBySlug: vi.fn(),
        setMapFilter: vi.fn(),
        setTermFilter: vi.fn(),
    };
}

describe("applyPendingSearch", () => {
    it("applies a saved search under its name without clearing separately", () => {
        const actions = buildActions();

        applyPendingSearch(
            {
                searchDefinition: {
                    terms: [],
                    queries: {},
                    graphSlugs: ["person"],
                    mapFilter: null,
                },
                searchName: "People",
            },
            actions,
        );

        expect(actions.applySearchDefinition).toHaveBeenCalledWith(
            {
                terms: [],
                queries: {},
                graphSlugs: ["person"],
                mapFilter: null,
                sort: [],
                includeRelated: true,
            },
            "People",
        );
        expect(actions.clearAll).not.toHaveBeenCalled();
    });

    it("starts a fresh search before adding a term", () => {
        const actions = buildActions();
        const callOrder: string[] = [];
        vi.mocked(actions.clearAll).mockImplementation(() => {
            callOrder.push("clearAll");
        });
        vi.mocked(actions.setTermFilter).mockImplementation(() => {
            callOrder.push("setTermFilter");
        });

        applyPendingSearch(
            {
                term: "Forbes",
                termKind: TERM_KIND_RECORD,
                termIcon: "fa fa-user",
            },
            actions,
        );

        expect(callOrder).toEqual(["clearAll", "setTermFilter"]);
        expect(actions.setTermFilter).toHaveBeenCalledWith({
            id: `${TERM_FILTER_KEY}:Forbes`,
            text: "Forbes",
            inverted: false,
            termKind: TERM_KIND_RECORD,
            icon: "fa fa-user",
        });
    });
});
