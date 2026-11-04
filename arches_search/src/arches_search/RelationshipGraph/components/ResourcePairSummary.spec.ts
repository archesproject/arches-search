import { enableAutoUnmount, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import ResourcePairSummary from "@/arches_search/RelationshipGraph/components/ResourcePairSummary.vue";
import { LOADED } from "@/arches_search/RelationshipGraph/utils/load-status.ts";

import type { RelationshipPath } from "@/arches_search/RelationshipGraph/types.ts";

function interpolate(text: string, values: Record<string, string> = {}) {
    return text.replace(/%\{(\w+)\}/g, (_match, key: string) => values[key]);
}

vi.mock("vue3-gettext", () => ({
    useGettext: () => ({
        $gettext: interpolate,
        $ngettext: (
            singular: string,
            plural: string,
            count: number,
            values: Record<string, string>,
        ) => interpolate(count === 1 ? singular : plural, values),
    }),
}));

function path(overrides: Partial<RelationshipPath> = {}): RelationshipPath {
    return {
        from_resource_id: "a",
        to_resource_id: "b",
        direct_relationships: [],
        direct_relationships_truncated: false,
        hops: 2,
        path_count: 1,
        relationship_ids: ["x", "y"],
        paths_truncated: false,
        max_hops: 6,
        limit_reached: false,
        ...overrides,
    };
}

function mountSummary(
    pathOverrides: Partial<RelationshipPath> = {},
    { isGraphVisible = true, isPathShown = false } = {},
) {
    return mount(ResourcePairSummary, {
        props: {
            fromTitle: "A",
            toTitle: "B",
            pathState: { status: LOADED, path: path(pathOverrides) },
            isPathShown,
            isGraphVisible,
        },
    });
}

enableAutoUnmount(afterEach);

describe("resource pair summary", () => {
    it("speaks of one path when there is one", () => {
        const wrapper = mountSummary();
        expect(wrapper.find(".hops").text()).toBe("2 hops apart");
        expect(wrapper.find(".path-toggle").text()).toBe(
            "Show the path in the graph",
        );
    });

    it("counts the shortest paths when there are several", () => {
        const wrapper = mountSummary({ path_count: 3 });
        expect(wrapper.find(".hops").text()).toBe("2 hops apart · 3 paths");
        expect(wrapper.find(".path-toggle").text()).toBe(
            "Show the paths in the graph",
        );
        expect(wrapper.find('[role="status"]').exists()).toBe(false);
    });

    it("says only some paths are drawn, while they are drawn", () => {
        const truncated = { path_count: 400, paths_truncated: true };
        expect(
            mountSummary(truncated, { isPathShown: true })
                .find('[role="status"]')
                .text(),
        ).toContain("Only some of the shortest paths are shown");
        for (const shown of [
            { isPathShown: false },
            { isPathShown: true, isGraphVisible: false },
        ]) {
            expect(
                mountSummary(truncated, shown).find('[role="status"]').exists(),
            ).toBe(false);
        }
    });

    it("offers the path toggle only while the graph is showing", () => {
        const wrapper = mountSummary(
            { path_count: 3 },
            { isGraphVisible: false },
        );
        expect(wrapper.find(".hops").text()).toBe("2 hops apart · 3 paths");
        expect(wrapper.find(".path-toggle").exists()).toBe(false);
    });
});
