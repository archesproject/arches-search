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

function descriptors(
    id: string,
    canEdit: boolean,
): Record<string, ResourceDescriptorData> {
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
            can_edit: canEdit,
        },
    };
}

describe("resource popup details", () => {
    afterEach(() => vi.resetAllMocks());

    it("exposes edit permission only after a successful response", async () => {
        vi.mocked(fetchResourceDescriptors).mockResolvedValue(
            descriptors("one", true),
        );
        const scope = effectScope();
        const state = scope.run(() => useResourceDescription("one"))!;
        expect(state.canEdit.value).toBe(false);
        await flushPromises();
        expect(state.description.value).toBe("one description");
        expect(state.canEdit.value).toBe(true);
        expect(fetchResourceDescriptors).toHaveBeenCalledWith(["one"], {
            includeCanEdit: true,
        });
        scope.stop();
    });

    it("does not grant edit permission to read-only resources", async () => {
        vi.mocked(fetchResourceDescriptors).mockResolvedValue(
            descriptors("one", false),
        );
        const scope = effectScope();
        const state = scope.run(() => useResourceDescription("one"))!;
        await flushPromises();
        expect(state.canEdit.value).toBe(false);
        expect(state.hasFailed.value).toBe(false);
        scope.stop();
    });

    it("clears permission on resource changes and ignores stale responses", async () => {
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
            .mockResolvedValueOnce(descriptors("two", false));
        const id = ref("one");
        const scope = effectScope();
        const state = scope.run(() => useResourceDescription(id))!;
        id.value = "two";
        await nextTick();
        await flushPromises();
        resolveFirst(descriptors("one", true));
        await flushPromises();
        expect(state.description.value).toBe("two description");
        expect(state.canEdit.value).toBe(false);
        scope.stop();
    });

    it("reports failure and leaves the editor unavailable", async () => {
        vi.mocked(fetchResourceDescriptors).mockRejectedValue(
            new Error("Unavailable"),
        );
        const scope = effectScope();
        const state = scope.run(() => useResourceDescription("one"))!;
        await flushPromises();
        expect(state.hasFailed.value).toBe(true);
        expect(state.isLoading.value).toBe(false);
        expect(state.canEdit.value).toBe(false);
        scope.stop();
    });
});
