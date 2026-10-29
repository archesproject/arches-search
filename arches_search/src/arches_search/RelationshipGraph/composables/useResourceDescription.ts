import { ref, toValue, watch } from "vue";

import arches from "arches";

import { fetchResourceDescriptors } from "@/arches_search/SearchResults/api.ts";

import type { MaybeRefOrGetter } from "vue";

// The description a resource's model configures for it, in the active
// language. It is a nicety, so a failure to get it only leaves it blank.
export function useResourceDescription(resourceId: MaybeRefOrGetter<string>) {
    const description = ref("");
    const isLoading = ref(false);

    let latestRequestId = 0;

    watch(
        () => toValue(resourceId),
        (id) => void loadDescription(id),
        { immediate: true },
    );

    async function loadDescription(id: string): Promise<void> {
        const requestId = ++latestRequestId;
        description.value = "";
        isLoading.value = true;
        try {
            const descriptors = await fetchResourceDescriptors([id]);
            if (requestId !== latestRequestId) return;
            description.value =
                descriptors[id]?.descriptors?.[arches.activeLanguage]
                    ?.description ?? "";
        } catch {
            // Left blank
        } finally {
            if (requestId === latestRequestId) isLoading.value = false;
        }
    }

    return { description, isLoading };
}
