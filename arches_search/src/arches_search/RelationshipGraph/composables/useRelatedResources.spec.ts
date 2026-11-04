import { nextTick, ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { fetchRelatedResources } from "@/arches_search/RelationshipGraph/api.ts";
import {
    RELATED_RESOURCES_PAGE_SIZE,
    useRelatedResources,
} from "@/arches_search/RelationshipGraph/composables/useRelatedResources.ts";

import type { RelatedResourcesPage } from "@/arches_search/RelationshipGraph/types.ts";

vi.mock("@/arches_search/RelationshipGraph/api.ts", () => ({
    fetchRelatedResources: vi.fn(),
}));

const fetchMock = vi.mocked(fetchRelatedResources);

function page(ids: string[], nextOffset: number | null): RelatedResourcesPage {
    return {
        resources: ids.map((id) => ({
            relationship_id: `x-${id}`,
            resource_id: id,
            name: `Resource ${id}`,
        })),
        next_offset: nextOffset,
    };
}

describe("useRelatedResources", () => {
    beforeEach(() => {
        fetchMock.mockReset();
    });

    it("appends pages in order and stops after the last one", async () => {
        fetchMock
            .mockResolvedValueOnce(page(["a", "b"], 2))
            .mockResolvedValueOnce(page(["c"], null));
        const { resources, hasMore, loadMore } = useRelatedResources(
            "seed",
            "row",
        );

        await loadMore();
        expect(hasMore.value).toBe(true);
        await loadMore();
        await loadMore();

        expect(resources.value.map((resource) => resource.resource_id)).toEqual(
            ["a", "b", "c"],
        );
        expect(hasMore.value).toBe(false);
        expect(fetchMock.mock.calls).toEqual([
            ["seed", "row", 0, RELATED_RESOURCES_PAGE_SIZE, ""],
            ["seed", "row", 2, RELATED_RESOURCES_PAGE_SIZE, ""],
        ]);
    });

    it("asks for one page at a time", async () => {
        let resolve: (value: RelatedResourcesPage) => void = () => {};
        fetchMock.mockReturnValueOnce(
            new Promise((resolvePage) => (resolve = resolvePage)),
        );
        const { isLoading, loadMore } = useRelatedResources("seed", "row");

        const first = loadMore();
        void loadMore();
        expect(isLoading.value).toBe(true);
        resolve(page(["a"], null));
        await first;

        expect(fetchMock).toHaveBeenCalledTimes(1);
        expect(isLoading.value).toBe(false);
    });

    it("keeps loaded pages when a later one fails, and retries it", async () => {
        fetchMock
            .mockResolvedValueOnce(page(["a"], 1))
            .mockRejectedValueOnce(new Error("offline"))
            .mockResolvedValueOnce(page(["b"], null));
        const { resources, hasFailed, loadMore } = useRelatedResources(
            "seed",
            "row",
        );

        await loadMore();
        await loadMore();
        expect(hasFailed.value).toBe(true);
        expect(resources.value).toHaveLength(1);

        await loadMore();
        expect(hasFailed.value).toBe(false);
        expect(fetchMock.mock.calls.at(-1)?.[2]).toBe(1);
        expect(resources.value).toHaveLength(2);
    });

    it("starts again from the first page when the term changes", async () => {
        fetchMock
            .mockResolvedValueOnce(page(["a", "b"], 2))
            .mockResolvedValueOnce(page(["b"], null));
        const term = ref("");
        const { resources, hasMore, loadMore } = useRelatedResources(
            "seed",
            "row",
            term,
        );

        await loadMore();
        term.value = "  Resource b ";
        await nextTick();
        await vi.waitFor(() => expect(hasMore.value).toBe(false));

        expect(fetchMock.mock.calls.at(-1)).toEqual([
            "seed",
            "row",
            0,
            RELATED_RESOURCES_PAGE_SIZE,
            "Resource b",
        ]);
        expect(resources.value.map((resource) => resource.resource_id)).toEqual(
            ["b"],
        );
    });

    it("throws away a page asked for under an earlier term", async () => {
        let resolveStale: (value: RelatedResourcesPage) => void = () => {};
        fetchMock
            .mockReturnValueOnce(
                new Promise((resolvePage) => (resolveStale = resolvePage)),
            )
            .mockResolvedValueOnce(page(["b"], null));
        const term = ref("");
        const { resources, isLoading, loadMore } = useRelatedResources(
            "seed",
            "row",
            term,
        );

        const stale = loadMore();
        term.value = "b";
        await nextTick();
        await vi.waitFor(() => expect(isLoading.value).toBe(false));
        resolveStale(page(["a"], 1));
        await stale;

        expect(resources.value.map((resource) => resource.resource_id)).toEqual(
            ["b"],
        );
        expect(isLoading.value).toBe(false);
    });
});
