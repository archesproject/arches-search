import { effectScope, nextTick } from "vue";
import { flushPromises } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchRelatedResources } from "@/arches_search/RelationshipGraph/api.ts";
import {
    RELATED_RESOURCES_PAGE_SIZE,
    useRelatedResources,
} from "@/arches_search/RelationshipGraph/composables/useRelatedResources.ts";

import type { EffectScope } from "vue";
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

function pendingPage(): {
    promise: Promise<RelatedResourcesPage>;
    resolve: (value: RelatedResourcesPage) => void;
} {
    let resolve: (value: RelatedResourcesPage) => void = () => {};
    const promise = new Promise<RelatedResourcesPage>((resolvePage) => {
        resolve = resolvePage;
    });
    return { promise, resolve };
}

describe("useRelatedResources", () => {
    let scope: EffectScope;

    function setUp(): ReturnType<typeof useRelatedResources> {
        scope = effectScope();
        return scope.run(() => useRelatedResources("seed", "row"))!;
    }

    beforeEach(() => {
        fetchMock.mockReset();
    });

    afterEach(() => {
        scope.stop();
        vi.useRealTimers();
    });

    it("loads the first page, appends the rest in order, and stops after the last one", async () => {
        fetchMock
            .mockResolvedValueOnce(page(["a", "b"], 2))
            .mockResolvedValueOnce(page(["c"], null));
        const { resources, hasMore, loadMore } = setUp();

        await flushPromises();
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
        const first = pendingPage();
        fetchMock.mockReturnValueOnce(first.promise);
        const { isLoading, loadMore } = setUp();

        void loadMore();
        expect(isLoading.value).toBe(true);
        first.resolve(page(["a"], null));
        await flushPromises();

        expect(fetchMock).toHaveBeenCalledTimes(1);
        expect(isLoading.value).toBe(false);
    });

    it("keeps loaded pages when a later one fails, and asks again only on retry", async () => {
        fetchMock
            .mockResolvedValueOnce(page(["a"], 1))
            .mockRejectedValueOnce(new Error("offline"))
            .mockResolvedValueOnce(page(["b"], null));
        const { resources, hasFailed, loadMore, retry } = setUp();

        await flushPromises();
        await loadMore();
        expect(hasFailed.value).toBe(true);
        expect(resources.value).toHaveLength(1);

        await loadMore();
        expect(fetchMock).toHaveBeenCalledTimes(2);

        await retry();
        expect(hasFailed.value).toBe(false);
        expect(fetchMock.mock.calls.at(-1)?.[2]).toBe(1);
        expect(resources.value).toHaveLength(2);
    });

    it("starts again from the first page once typing pauses", async () => {
        fetchMock
            .mockResolvedValueOnce(page(["a", "b"], 2))
            .mockResolvedValueOnce(page(["b"], null));
        const { filterText, resources, hasMore } = setUp();
        await flushPromises();

        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        filterText.value = "Res";
        await nextTick();
        filterText.value = "  Resource b ";
        await nextTick();
        vi.runAllTimers();
        await flushPromises();

        expect(fetchMock.mock.calls).toEqual([
            ["seed", "row", 0, RELATED_RESOURCES_PAGE_SIZE, ""],
            ["seed", "row", 0, RELATED_RESOURCES_PAGE_SIZE, "Resource b"],
        ]);
        expect(resources.value.map((resource) => resource.resource_id)).toEqual(
            ["b"],
        );
        expect(hasMore.value).toBe(false);
    });

    it("throws away a page asked for under an earlier term", async () => {
        const stale = pendingPage();
        fetchMock
            .mockReturnValueOnce(stale.promise)
            .mockResolvedValueOnce(page(["b"], null));
        const { filterText, resources, isLoading } = setUp();

        vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
        filterText.value = "b";
        await nextTick();
        vi.runAllTimers();
        await flushPromises();
        stale.resolve(page(["a"], 1));
        await flushPromises();

        expect(resources.value.map((resource) => resource.resource_id)).toEqual(
            ["b"],
        );
        expect(isLoading.value).toBe(false);
    });
});
