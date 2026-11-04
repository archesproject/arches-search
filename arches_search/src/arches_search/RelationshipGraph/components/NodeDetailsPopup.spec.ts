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
    isSeed: false,
};

function mountPopup(
    props: Partial<typeof PROPS> = {},
    viewRelatedResource: unknown = vi.fn(),
) {
    return mount(NodeDetailsPopup, {
        props: { ...PROPS, ...props },
        global: { provide: { viewRelatedResource } },
    });
}

function actionLabels(wrapper: ReturnType<typeof mountPopup>): string[] {
    return wrapper.findAll(".actions > *").map((action) => action.text());
}

describe("node details popup", () => {
    afterEach(() => vi.resetAllMocks());

    it("offers the report and focus, and no editor", async () => {
        vi.mocked(fetchResourceDescriptors).mockResolvedValue({
            resource: { descriptors: {}, graph_id: "model" },
        });
        const wrapper = mountPopup();
        await flushPromises();
        expect(actionLabels(wrapper)).toEqual(["View Report", "Focus"]);
        expect(wrapper.find(".name").text()).toBe(PROPS.name);
        expect(wrapper.find("img").exists()).toBe(false);
        wrapper.unmount();
    });

    it("adds the resource to the panel when focused", async () => {
        vi.mocked(fetchResourceDescriptors).mockResolvedValue({});
        const viewRelatedResource = vi.fn();
        const wrapper = mountPopup({}, viewRelatedResource);
        await wrapper.find("button").trigger("click");
        expect(viewRelatedResource).toHaveBeenCalledWith({
            id: PROPS.resourceId,
            title: PROPS.name,
        });
        wrapper.unmount();
    });

    it("has nothing to focus for a resource already in the panel, or outside the search page", async () => {
        vi.mocked(fetchResourceDescriptors).mockResolvedValue({});
        for (const wrapper of [
            mountPopup({ isSeed: true }),
            mountPopup({}, null),
        ]) {
            await flushPromises();
            expect(actionLabels(wrapper)).toEqual(["View Report"]);
            wrapper.unmount();
        }
    });

    it("announces loading failures and still offers the report", async () => {
        vi.mocked(fetchResourceDescriptors).mockRejectedValue(
            new Error("Unavailable"),
        );
        const wrapper = mountPopup();
        await flushPromises();
        expect(wrapper.find('[role="status"]').text()).toContain(
            "could not be loaded",
        );
        expect(actionLabels(wrapper)).toEqual(["View Report", "Focus"]);
        wrapper.unmount();
    });
});
