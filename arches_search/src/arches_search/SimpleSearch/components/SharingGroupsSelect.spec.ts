import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import OpenVue from "openvue/config";
import MultiSelect from "openvue/multiselect";

import SharingGroupsSelect from "@/arches_search/SimpleSearch/components/SharingGroupsSelect.vue";

import { getSharingGroups } from "@/arches_search/SimpleSearch/api.ts";

vi.mock("@/arches_search/SimpleSearch/api.ts", () => ({
    getSharingGroups: vi.fn(),
}));

function mountSelect() {
    return mount(SharingGroupsSelect, {
        props: { sharedGroupIds: [], inputId: "groups-input" },
        global: { plugins: [OpenVue] },
    });
}

describe("SharingGroupsSelect", () => {
    afterEach(() => vi.resetAllMocks());

    it("offers the loaded groups and emits the selection", async () => {
        const groups = [{ id: 1, name: "Resource Reviewer" }];
        vi.mocked(getSharingGroups).mockResolvedValue(groups);
        const wrapper = mountSelect();
        await flushPromises();

        const multiSelect = wrapper.findComponent(MultiSelect);
        expect(multiSelect.props("options")).toEqual(groups);

        multiSelect.vm.$emit("update:modelValue", [1]);
        expect(wrapper.emitted("update:sharedGroupIds")).toEqual([[[1]]]);
    });

    it("says so when the groups fail to load", async () => {
        vi.mocked(getSharingGroups).mockRejectedValue(new Error("Forbidden"));
        const wrapper = mountSelect();
        await flushPromises();

        expect(wrapper.find(".sharing-groups-error").exists()).toBe(true);
    });
});
