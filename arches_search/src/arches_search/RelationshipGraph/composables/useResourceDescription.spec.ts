import { effectScope, nextTick, ref } from "vue";
import { flushPromises } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchResourceDescriptors } from "@/arches_search/SearchResults/api.ts";
import { useResourceDescription } from "@/arches_search/RelationshipGraph/composables/useResourceDescription.ts";

import type { ResourceDescriptorData } from "@/arches_search/SearchResults/types.ts";

vi.mock("arches", () => ({ default: { activeLanguage: "en" } }));
vi.mock("@/arches_search/SearchResults/api.ts", () => ({
    fetchResourceDescriptors: vi.fn(),
}));

function descriptors(id: string): Record<string, ResourceDescriptorData> {
    return {
        [id]: {
            descriptors: {
                en: {
                    name: id,
                    description: `${id} description`,
                    map_popup: "",
                },
            },
            graph_id: "model",
            has_geometry: false,
            lifecycle_state_id: null,
        },
    };
}

describe("resource popup details", () => {
    afterEach(() => vi.resetAllMocks());

    it("loads the description in the active language", async () => {
        vi.mocked(fetchResourceDescriptors).mockResolvedValue(
            descriptors("one"),
        );
        const scope = effectScope();
        const state = scope.run(() => useResourceDescription("one"))!;
        expect(state.isLoading.value).toBe(true);
        await flushPromises();
        expect(state.description.value).toBe("one description");
        expect(state.isLoading.value).toBe(false);
        expect(state.hasFailed.value).toBe(false);
        expect(fetchResourceDescriptors).toHaveBeenCalledWith(["one"]);
        scope.stop();
    });

    it("ignores a response for a resource it has moved on from", async () => {
        let resolveFirst: (
            value: Record<string, ResourceDescriptorData>,
        ) => void = () => {};
        vi.mocked(fetchResourceDescriptors)
            .mockImplementationOnce(
                () =>
                    new Promise((resolve) => {
                        resolveFirst = resolve;
                    }),
            )
            .mockResolvedValueOnce(descriptors("two"));
        const id = ref("one");
        const scope = effectScope();
        const state = scope.run(() => useResourceDescription(id))!;
        id.value = "two";
        await nextTick();
        await flushPromises();
        resolveFirst(descriptors("one"));
        await flushPromises();
        expect(state.description.value).toBe("two description");
        scope.stop();
    });

    it("reports failure", async () => {
        vi.mocked(fetchResourceDescriptors).mockRejectedValue(
            new Error("Unavailable"),
        );
        const scope = effectScope();
        const state = scope.run(() => useResourceDescription("one"))!;
        await flushPromises();
        expect(state.hasFailed.value).toBe(true);
        expect(state.isLoading.value).toBe(false);
        expect(state.description.value).toBe("");
        scope.stop();
    });
});
