import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import OpenVue from "openvue/config";
import Button from "openvue/button";

import SavedSearchList from "@/arches_search/SimpleSearch/components/SavedSearchList.vue";
import SharingGroupsSelect from "@/arches_search/SimpleSearch/components/SharingGroupsSelect.vue";

import {
    deleteSavedSearch,
    getSavedSearches,
    getSharingGroups,
    updateSavedSearchGroups,
} from "@/arches_search/SimpleSearch/api.ts";

import type { VueWrapper } from "@vue/test-utils";

import type { SavedSearch } from "@/arches_search/SimpleSearch/types.ts";

const { requireConfirmation } = vi.hoisted(() => ({
    requireConfirmation: vi.fn(),
}));

vi.mock("vue3-gettext", () => ({
    useGettext: () => ({
        $gettext: (text: string, values: Record<string, string> = {}) =>
            text.replace(/%\{(\w+)\}/g, (_match, key) => values[key]),
    }),
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
    getSharingGroups: vi.fn(),
    updateSavedSearchGroups: vi.fn(),
}));

const MILLS: SavedSearch = {
    savedsearchid: "mills",
    name: "Mills",
    description: "",
    query_definition: { resourceSetId: "set-1" },
    created_at: "2026-01-02T00:00:00Z",
    creator: { id: 1, username: "admin" },
    shared_groups: [
        { id: 1, name: "Resource Editor" },
        { id: 2, name: "Resource Reviewer" },
    ],
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

type ListWrapper = Awaited<ReturnType<typeof mountList>>;

function findButton(
    wrapper: ListWrapper,
    label: string,
): ButtonWrapper | undefined {
    return wrapper
        .findAllComponents(Button)
        .find((button: ButtonWrapper) => button.props("label") === label);
}

beforeEach(() => {
    vi.stubGlobal("matchMedia", () => ({
        matches: false,
        addEventListener: () => {},
        removeEventListener: () => {},
    }));
    vi.mocked(getSavedSearches).mockResolvedValue([MILLS]);
    vi.mocked(getSharingGroups).mockResolvedValue([]);
});

afterEach(() => {
    vi.resetAllMocks();
    vi.unstubAllGlobals();
});

describe("SavedSearchList deleting", () => {
    it("deletes only after you confirm", async () => {
        vi.mocked(deleteSavedSearch).mockResolvedValue(undefined);
        const wrapper = await mountList();

        await findButton(wrapper, "Delete")!.trigger("click");
        expect(deleteSavedSearch).not.toHaveBeenCalled();

        requireConfirmation.mock.lastCall![0].accept();
        await flushPromises();

        expect(deleteSavedSearch).toHaveBeenCalledWith("mills");
        expect(wrapper.find(".saved-search-item").exists()).toBe(false);
    });

    it("does not let you delete others' searches", async () => {
        const wrapper = await mountList("shared");

        expect(findButton(wrapper, "Delete")).toBeUndefined();
    });
});

describe("SavedSearchList sharing", () => {
    it("lists the groups an own search is shared with", async () => {
        const wrapper = await mountList();

        expect(wrapper.find(".item-shared").text()).toBe(
            "Shared with: Resource Editor, Resource Reviewer",
        );
    });

    it("does not let you share others' searches", async () => {
        const wrapper = await mountList("shared");

        expect(findButton(wrapper, "Share")).toBeUndefined();
    });

    it("opens the sharing editor with the current groups chosen", async () => {
        const wrapper = await mountList();

        await findButton(wrapper, "Share")!.trigger("click");

        expect(
            wrapper.findComponent(SharingGroupsSelect).props("sharedGroupIds"),
        ).toEqual([1, 2]);
    });

    it("saves the chosen groups and shows them", async () => {
        vi.mocked(updateSavedSearchGroups).mockResolvedValue({
            ...MILLS,
            shared_groups: [{ id: 3, name: "Crowdsource Editor" }],
        });
        const wrapper = await mountList();
        await findButton(wrapper, "Share")!.trigger("click");
        wrapper
            .findComponent(SharingGroupsSelect)
            .vm.$emit("update:sharedGroupIds", [3]);

        await findButton(wrapper, "Save sharing")!.trigger("click");
        await flushPromises();

        expect(updateSavedSearchGroups).toHaveBeenCalledWith("mills", [3]);
        expect(wrapper.find(".item-shared").text()).toBe(
            "Shared with: Crowdsource Editor",
        );
        expect(wrapper.find(".item-sharing-editor").exists()).toBe(false);
    });
});
