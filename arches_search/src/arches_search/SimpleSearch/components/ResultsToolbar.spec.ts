import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import ResultsToolbar from "@/arches_search/SimpleSearch/components/ResultsToolbar.vue";

import {
    RESULTS_SORT_CREATED_TIME,
    RESULTS_SORT_NAME,
    RESULTS_SORT_RELEVANCE,
} from "@/arches_search/SimpleSearch/types.ts";
import type {
    NodeFilterConfigNode,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";

// The toolbar only reads shared search state, so give it a fixed copy.
vi.mock(
    "@/arches_search/SimpleSearch/composables/useSearchFilters.ts",
    async () => {
        const { ref } = await import("vue");
        return {
            useSearchFilters: () => ({
                includeRelated: ref(false),
                searchResults: ref({ pagination: { total_results: 3 } }),
                setIncludeRelated: () => {},
            }),
        };
    },
);

// Stand-ins for the UI library's components; the select records the options it
// is given so the test can read them.
vi.mock("openvue/select", () => ({
    default: {
        name: "SelectStub",
        props: { options: { type: Array, default: () => [] } },
        template: "<div />",
    },
}));

vi.mock("openvue/toggleswitch", () => ({
    default: {
        name: "ToggleSwitchStub",
        template: "<input type='checkbox' />",
    },
}));

vi.mock("openvue/button", () => ({
    default: {
        name: "ButtonStub",
        props: { label: { type: String, default: "" } },
        template: "<button type='button'>{{ label }}</button>",
    },
}));

function mountToolbar(sortableNodes: NodeFilterConfigNode[] = []) {
    return mount(ResultsToolbar, {
        props: {
            sortField: RESULTS_SORT_NAME,
            sortDirection: "asc",
            sortableNodes,
            showFilters: false,
            showMap: false,
            hasMapFilter: false,
            showTime: false,
            hasTimeFilter: false,
            showSavedSearches: false,
            showExportResults: false,
        },
    });
}

describe("ResultsToolbar sorting", () => {
    it("offers the built-in sorts plus one option per sortable node", () => {
        const wrapper = mountToolbar([
            { node_alias: "nationality", label: "Nationality" },
        ] as NodeFilterConfigNode[]);

        const options: SortOption[] = wrapper
            .findComponent({ name: "SelectStub" })
            .props("options");

        expect(options).toEqual([
            { label: "Relevance", value: RESULTS_SORT_RELEVANCE },
            { label: "Title", value: RESULTS_SORT_NAME },
            { label: "Date created", value: RESULTS_SORT_CREATED_TIME },
            { label: "Nationality", value: "node:nationality" },
        ]);
    });

    it("emits the opposite direction when the direction button is clicked", async () => {
        const wrapper = mountToolbar();

        await wrapper.find(".sort-direction-btn").trigger("click");
        await wrapper.setProps({ sortDirection: "desc" });
        await wrapper.find(".sort-direction-btn").trigger("click");

        expect(wrapper.emitted("update:sortDirection")).toEqual([
            ["desc"],
            ["asc"],
        ]);
    });
});
