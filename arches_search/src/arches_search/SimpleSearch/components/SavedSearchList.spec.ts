import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import OpenVue from "openvue/config";
import Button from "openvue/button";

import SavedSearchList from "@/arches_search/SimpleSearch/components/SavedSearchList.vue";

import {
    deleteSavedSearch,
    getSavedSearches,
} from "@/arches_search/SimpleSearch/api.ts";

import type { VueWrapper } from "@vue/test-utils";

import type { SavedSearch } from "@/arches_search/SimpleSearch/types.ts";

const { requireConfirmation } = vi.hoisted(() => ({
    requireConfirmation: vi.fn(),
}));

vi.mock("openvue/usetoast", () => ({
    useToast: () => ({ add: vi.fn() }),
}));

vi.mock("openvue/useconfirm", () => ({
    useConfirm: () => ({ require: requireConfirmation }),
}));

vi.mock("@/arches_search/SimpleSearch/api.ts", () => ({
    deleteSavedSearch: vi.fn(),
    getSavedSearches: vi.fn(),
}));

const MILLS: SavedSearch = {
    savedsearchid: "mills",
    name: "Mills",
    description: "",
    query_definition: { resourceSetId: "set-1" },
    created_at: "2026-01-02T00:00:00Z",
    creator: { id: 1, username: "admin" },
};

type ButtonWrapper = VueWrapper<InstanceType<typeof Button>>;

async function mountList(scope: "mine" | "shared" = "mine") {
    const wrapper = mount(SavedSearchList, {
        props: { scope },
        global: { plugins: [OpenVue] },
    });
    await flushPromises();
    return wrapper;
}

function findDeleteButton(
    wrapper: Awaited<ReturnType<typeof mountList>>,
): ButtonWrapper | undefined {
    return wrapper
        .findAllComponents(Button)
        .find((button: ButtonWrapper) => button.props("label") === "Delete");
}

describe("SavedSearchList deleting", () => {
    beforeEach(() => {
        vi.stubGlobal("matchMedia", () => ({
            matches: false,
            addEventListener: () => {},
            removeEventListener: () => {},
        }));
        vi.mocked(getSavedSearches).mockResolvedValue([MILLS]);
    });

    afterEach(() => {
        vi.resetAllMocks();
        vi.unstubAllGlobals();
    });

    it("deletes only after you confirm", async () => {
        vi.mocked(deleteSavedSearch).mockResolvedValue(undefined);
        const wrapper = await mountList();

        await findDeleteButton(wrapper)!.trigger("click");
        expect(deleteSavedSearch).not.toHaveBeenCalled();

        requireConfirmation.mock.lastCall![0].accept();
        await flushPromises();

        expect(deleteSavedSearch).toHaveBeenCalledWith("mills");
        expect(wrapper.find(".saved-search-item").exists()).toBe(false);
    });

    it("does not let you delete others' searches", async () => {
        const wrapper = await mountList("shared");

        expect(findDeleteButton(wrapper)).toBeUndefined();
    });
});
