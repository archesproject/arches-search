import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import OpenVue from "openvue/config";
import MultiSelect from "openvue/multiselect";

import SharingGroupsSelect from "@/arches_search/SimpleSearch/components/SharingGroupsSelect.vue";

describe("SharingGroupsSelect", () => {
    it("offers the given groups and emits the selection", () => {
        const groups = [{ id: 1, name: "Resource Reviewer" }];
        const wrapper = mount(SharingGroupsSelect, {
            props: { sharedGroupIds: [], inputId: "groups-input", groups },
            global: { plugins: [OpenVue] },
        });

        const multiSelect = wrapper.findComponent(MultiSelect);
        expect(multiSelect.props("options")).toEqual(groups);

        multiSelect.vm.$emit("update:modelValue", [1]);
        expect(wrapper.emitted("update:sharedGroupIds")).toEqual([[[1]]]);
    });
});
