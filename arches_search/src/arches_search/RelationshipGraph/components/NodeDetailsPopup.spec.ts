import { mount, flushPromises } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import NodeDetailsPopup from "@/arches_search/RelationshipGraph/components/NodeDetailsPopup.vue";
import { fetchResourceDescriptors } from "@/arches_search/SearchResults/api.ts";

vi.mock("@/arches_search/SearchResults/api.ts", () => ({
    fetchResourceDescriptors: vi.fn(),
}));
vi.mock("@/arches_vue_components/application", () => ({
    generateArchesURL: (name: string) => `/${name}`,
}));
vi.mock("arches", () => ({ default: { activeLanguage: "en" } }));
vi.mock("vue3-gettext", () => ({
    useGettext: () => ({
        $gettext: (text: string) => text,
        $ngettext: (singular: string, plural: string, count: number) =>
            count === 1 ? singular : plural,
    }),
}));

const PROPS = {
    resourceId: "resource",
    name: "<img src=x onerror=alert(1)>",
    modelName: "Model",
    modelColor: "var(--p-primary-color)",
    relatedCount: 1,
};

describe("node details popup", () => {
    afterEach(() => vi.resetAllMocks());

    it("keeps the report link but hides edit for a read-only resource", async () => {
        vi.mocked(fetchResourceDescriptors).mockResolvedValue({
            resource: { descriptors: {}, graph_id: "model", can_edit: false },
        });
        const wrapper = mount(NodeDetailsPopup, { props: PROPS });
        await flushPromises();
        expect(wrapper.findAll("a").map((link) => link.text())).toEqual([
            "View Report",
        ]);
        expect(wrapper.find(".name").text()).toBe(PROPS.name);
        expect(wrapper.find("img").exists()).toBe(false);
        wrapper.unmount();
    });

    it("shows edit only after the server grants it", async () => {
        vi.mocked(fetchResourceDescriptors).mockResolvedValue({
            resource: { descriptors: {}, graph_id: "model", can_edit: true },
        });
        const wrapper = mount(NodeDetailsPopup, { props: PROPS });
        expect(wrapper.findAll("a")).toHaveLength(1);
        await flushPromises();
        expect(wrapper.findAll("a").map((link) => link.text())).toEqual([
            "View Report",
            "Edit",
        ]);
        wrapper.unmount();
    });

    it("announces loading failures and does not expose edit", async () => {
        vi.mocked(fetchResourceDescriptors).mockRejectedValue(
            new Error("Unavailable"),
        );
        const wrapper = mount(NodeDetailsPopup, { props: PROPS });
        await flushPromises();
        expect(wrapper.find('[role="status"]').text()).toContain(
            "could not be loaded",
        );
        expect(wrapper.findAll("a")).toHaveLength(1);
        wrapper.unmount();
    });
});
