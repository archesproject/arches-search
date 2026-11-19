import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import OpenVue from "openvue/config";

import SaveSearchForm from "@/arches_search/SimpleSearch/components/SaveSearchForm.vue";

import {
    getResourceSetLimits,
    saveResultsAsResourceSet,
} from "@/arches_search/SimpleSearch/api.ts";

import type { SearchResultsToSave } from "@/arches_search/SimpleSearch/types.ts";

vi.mock("openvue/usetoast", () => ({
    useToast: () => ({ add: vi.fn() }),
}));

vi.mock("@/arches_search/SimpleSearch/api.ts", () => ({
    createSavedSearch: vi.fn(),
    getResourceSetLimits: vi.fn(),
    saveResultsAsResourceSet: vi.fn(),
}));

const RESULTS: SearchResultsToSave = {
    queries: [],
    graphSlugs: ["heritage_resource"],
};

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

describe("SaveSearchForm saving results", () => {
    beforeEach(() => {
        vi.mocked(getResourceSetLimits).mockResolvedValue({
            immediate_threshold: 10,
            member_limit: 100,
        });
    });

    afterEach(() => vi.resetAllMocks());

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
        });
    });

    it("won't save more results than the member limit", async () => {
        const wrapper = await mountResultsForm(101);

        expect(
            (saveButton(wrapper).element as HTMLButtonElement).disabled,
        ).toBe(true);
    });
});
