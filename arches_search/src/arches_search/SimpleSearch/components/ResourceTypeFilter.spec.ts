import { ref } from "vue";

import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import ResourceTypeFilter from "@/arches_search/SimpleSearch/components/ResourceTypeFilter.vue";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type { VueWrapper } from "@vue/test-utils";
import type { SearchResults } from "@/arches_search/AdvancedSearch/types.ts";
import type { ResourceType } from "@/arches_search/SimpleSearch/types.ts";

vi.mock("@/arches_search/SimpleSearch/composables/useSearchFilters.ts", () => ({
    useSearchFilters: vi.fn(),
}));

// The shared setup's gettext returns text untouched; counts need interpolating.
vi.mock("vue3-gettext", () => ({
    useGettext: () => ({
        $gettext: (text: string, parameters: Record<string, string> = {}) =>
            text.replace(
                /%\{(\w+)\}/g,
                (_placeholder, key: string) => parameters[key],
            ),
        current: "en",
    }),
}));

const SITE_GRAPH_ID = "site-graph-id";
const PERSON_GRAPH_ID = "person-graph-id";

const SITE: ResourceType = {
    id: SITE_GRAPH_ID,
    slug: "site",
    label: "Site",
    icon: "",
};
const PERSON: ResourceType = {
    id: PERSON_GRAPH_ID,
    slug: "person",
    label: "Person",
    icon: "",
};

const ButtonStub = { name: "Button", template: "<button><slot /></button>" };

interface GraphCount {
    graphId: string;
    count: number;
}

function searchResultsWith(
    totalResults: number,
    graphCounts: GraphCount[],
): SearchResults {
    return {
        resources: [],
        aggregations: {},
        pagination: {
            page: 1,
            page_size: 20,
            total_results: totalResults,
            total_pages: 1,
            has_next: false,
            has_previous: false,
        },
        resource_type_counts: graphCounts.map(({ graphId, count }) => ({
            graph_id: graphId,
            name: graphId,
            icon: "",
            count,
        })),
    };
}

function mountWithSearch(
    activeGraphs: ResourceType[],
    searchResults: SearchResults,
): VueWrapper {
    vi.mocked(useSearchFilters).mockReturnValue({
        activeGraphs: ref(activeGraphs),
        availableGraphs: ref([SITE, PERSON]),
        loadAvailableGraphs: vi.fn().mockResolvedValue(undefined),
        searchResults: ref(searchResults),
        toggleGraph: vi.fn(),
    } as unknown as ReturnType<typeof useSearchFilters>);

    return mount(ResourceTypeFilter, {
        global: { stubs: { Button: ButtonStub } },
    });
}

function countsByLabel(wrapper: VueWrapper): Record<string, string | null> {
    return Object.fromEntries(
        wrapper.findAll("button").map((button) => {
            const count = button.find(".type-count");
            return [
                button.find(".type-label").text(),
                count.exists() ? count.text() : null,
            ];
        }),
    );
}

describe("ResourceTypeFilter counts", () => {
    it("counts every resource type, and the total, when All is selected", () => {
        const wrapper = mountWithSearch(
            [],
            searchResultsWith(8, [
                { graphId: SITE_GRAPH_ID, count: 3 },
                { graphId: PERSON_GRAPH_ID, count: 5 },
            ]),
        );

        expect(countsByLabel(wrapper)).toEqual({
            All: "(8)",
            Site: "(3)",
            Person: "(5)",
        });
    });

    it("counts only the resource types the search included", () => {
        const wrapper = mountWithSearch(
            [SITE],
            searchResultsWith(3, [{ graphId: SITE_GRAPH_ID, count: 3 }]),
        );

        expect(countsByLabel(wrapper)).toEqual({
            All: null,
            Site: "(3)",
            Person: null,
        });
    });

    it("shows zero for an included resource type with no matches", () => {
        const wrapper = mountWithSearch(
            [PERSON],
            searchResultsWith(0, [{ graphId: PERSON_GRAPH_ID, count: 0 }]),
        );

        expect(countsByLabel(wrapper)).toEqual({
            All: null,
            Site: null,
            Person: "(0)",
        });
    });

    it("leaves the count out of an uncounted resource type's tooltip", () => {
        const wrapper = mountWithSearch(
            [SITE],
            searchResultsWith(3, [{ graphId: SITE_GRAPH_ID, count: 3 }]),
        );
        const titles = wrapper
            .findAll("button")
            .map((button) => button.attributes("title"));

        expect(titles).toEqual(["All", "Site — 3 records", "Person"]);
    });
});
