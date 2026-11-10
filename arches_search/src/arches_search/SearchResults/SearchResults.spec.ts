import { defineComponent, h } from "vue";
import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import SearchResults from "@/arches_search/SearchResults/SearchResults.vue";
import { provideResultsMapSelection } from "@/arches_search/SimpleSearch/composables/useResultsMapSelection.ts";

import type { SearchResults as SearchResultsData } from "@/arches_search/AdvancedSearch/types.ts";
import type { ResultsMapSelection } from "@/arches_search/SimpleSearch/composables/useResultsMapSelection.ts";

vi.mock("@/arches_search/SearchResults/api.ts", () => ({
    fetchResourceDescriptors: vi.fn().mockResolvedValue({}),
    fetchResourceInstanceLifecycleStates: vi.fn().mockResolvedValue([]),
    fetchSearchReportConfig: vi.fn().mockResolvedValue(null),
}));

vi.mock("@/arches_search/SearchResults/SearchResultCard.vue", () => ({
    default: {
        name: "SearchResultCardStub",
        props: { resourceInstanceId: { type: String, required: true } },
        template: "<div class='card-stub'>{{ resourceInstanceId }}</div>",
    },
}));

vi.mock("openvue/button", () => ({
    default: {
        name: "ButtonStub",
        props: { label: { type: String, default: "" } },
        template: "<button type='button'>{{ label }}</button>",
    },
}));

vi.mock("openvue/skeleton", () => ({
    default: { name: "SkeletonStub", template: "<div />" },
}));

function searchResultsFor(resourceIds: string[]): SearchResultsData {
    return {
        resources: resourceIds.map((resourceId) => ({
            resourceinstanceid: resourceId,
            createdtime: "",
            graph_id: "graph",
        })),
        aggregations: {},
        pagination: {
            page: 1,
            page_size: resourceIds.length,
            total_results: resourceIds.length,
            total_pages: 1,
            has_next: false,
            has_previous: false,
        },
    };
}

function mountWithSelection(resourceIds: string[]): {
    wrapper: ReturnType<typeof mount>;
    selection: ResultsMapSelection;
} {
    let selection: ResultsMapSelection | null = null;
    const Host = defineComponent({
        setup() {
            selection = provideResultsMapSelection({ openMap: vi.fn() });
            return () =>
                h(SearchResults, {
                    results: searchResultsFor(resourceIds),
                    isSearching: false,
                    graphModels: [],
                });
        },
    });
    const wrapper = mount(Host);
    return { wrapper, selection: selection! };
}

function cardOrder(wrapper: ReturnType<typeof mount>): string[] {
    return wrapper.findAll(".card-stub").map((card) => card.text());
}

describe("search results with a record pinned from the map", () => {
    it("lists the pinned record first, without a duplicate, until it is unpinned", async () => {
        const { wrapper, selection } = mountWithSelection([
            "first",
            "second",
            "third",
        ]);
        await flushPromises();
        expect(cardOrder(wrapper)).toEqual(["first", "second", "third"]);

        selection.pinnedResourceId.value = "second";
        await flushPromises();
        expect(cardOrder(wrapper)).toEqual(["second", "first", "third"]);

        await wrapper.find(".search-results-unpin").trigger("click");
        expect(cardOrder(wrapper)).toEqual(["first", "second", "third"]);
    });
});
