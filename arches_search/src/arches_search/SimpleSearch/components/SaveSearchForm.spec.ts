import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import OpenVue from "openvue/config";
import Button from "openvue/button";

import SaveSearchForm from "@/arches_search/SimpleSearch/components/SaveSearchForm.vue";
import SharingGroupsSelect from "@/arches_search/SimpleSearch/components/SharingGroupsSelect.vue";

import {
    createSavedSearch,
    getResourceSetLimits,
    getSharingGroups,
    saveResultsAsResourceSet,
} from "@/arches_search/SimpleSearch/api.ts";

import type {
    SavedSearch,
    SearchDefinition,
    SearchResultsToSave,
} from "@/arches_search/SimpleSearch/types.ts";

vi.mock("openvue/usetoast", () => ({
    useToast: () => ({ add: vi.fn() }),
}));

vi.mock("@/arches_search/SimpleSearch/api.ts", () => ({
    createSavedSearch: vi.fn(),
    getResourceSetLimits: vi.fn(),
    getSharingGroups: vi.fn(),
    saveResultsAsResourceSet: vi.fn(),
}));

const DEFINITION = { graphSlugs: [] } as unknown as SearchDefinition;

const RESULTS: SearchResultsToSave = {
    queries: [],
    graphSlugs: ["heritage_resource"],
};

beforeEach(() => {
    vi.mocked(getSharingGroups).mockResolvedValue([]);
    vi.mocked(getResourceSetLimits).mockResolvedValue({
        immediate_threshold: 10,
        member_limit: 100,
    });
});

afterEach(() => vi.resetAllMocks());

describe("SaveSearchForm saving results", () => {
    async function mountResultsForm(resultCount: number) {
        const wrapper = mount(SaveSearchForm, {
            props: { resultsToSave: RESULTS, resultCount },
            global: { plugins: [OpenVue] },
        });
        await wrapper.find("#save-as-results").setValue(true);
        await wrapper.find("#save-search-name").setValue("Mills");
        await flushPromises();
        return wrapper;
    }

    function saveButton(wrapper: Awaited<ReturnType<typeof mountResultsForm>>) {
        return wrapper.find(".save-form-actions button");
    }

    it("saves the search's results as a set", async () => {
        vi.mocked(saveResultsAsResourceSet).mockResolvedValue({
            message: "Saved",
        });
        const wrapper = await mountResultsForm(5);

        await saveButton(wrapper).trigger("click");
        await flushPromises();

        expect(saveResultsAsResourceSet).toHaveBeenCalledWith({
            ...RESULTS,
            name: "Mills",
            description: "",
            groupIds: [],
        });
    });

    it("won't save more results than the member limit", async () => {
        const wrapper = await mountResultsForm(101);

        expect(
            (saveButton(wrapper).element as HTMLButtonElement).disabled,
        ).toBe(true);
    });
});

describe("SaveSearchForm sharing", () => {
    function mountForm() {
        return mount(SaveSearchForm, {
            props: {
                definitionToSave: DEFINITION,
                resultsToSave: RESULTS,
                resultCount: 5,
            },
            global: { plugins: [OpenVue] },
        });
    }

    async function saveSharedWith(
        wrapper: ReturnType<typeof mountForm>,
        groupIds: number[],
    ): Promise<void> {
        wrapper
            .findComponent(SharingGroupsSelect)
            .vm.$emit("update:sharedGroupIds", groupIds);
        await wrapper.find("#save-search-name").setValue("Mills");
        await wrapper
            .find(".save-form-actions")
            .findComponent(Button)
            .trigger("click");
        await flushPromises();
    }

    it("shares a saved query with the chosen groups, then clears them", async () => {
        vi.mocked(createSavedSearch).mockResolvedValue({} as SavedSearch);
        const wrapper = mountForm();

        await saveSharedWith(wrapper, [3]);

        expect(createSavedSearch).toHaveBeenCalledWith(
            "Mills",
            "",
            DEFINITION,
            [3],
        );
        expect(
            wrapper.findComponent(SharingGroupsSelect).props("sharedGroupIds"),
        ).toEqual([]);
    });

    it("shares saved results with the chosen groups", async () => {
        vi.mocked(saveResultsAsResourceSet).mockResolvedValue({
            message: "Saved",
        });
        const wrapper = mountForm();
        await wrapper.find("#save-as-results").setValue(true);
        await flushPromises();

        await saveSharedWith(wrapper, [1, 2]);

        expect(saveResultsAsResourceSet).toHaveBeenCalledWith(
            expect.objectContaining({ groupIds: [1, 2] }),
        );
    });
});
