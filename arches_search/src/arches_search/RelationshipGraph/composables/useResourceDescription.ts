import { ref, toValue, watch } from "vue";

import arches from "arches";

import { fetchResourceDescriptors } from "@/arches_search/SearchResults/api.ts";

import type { MaybeRefOrGetter } from "vue";

// The description a resource's model configures for it, in the active
// language, with permission to expose the editor link.
export function useResourceDescription(resourceId: MaybeRefOrGetter<string>) {
    const description = ref("");
    const isLoading = ref(false);
    const canEdit = ref(false);
    const hasFailed = ref(false);

    let latestRequestId = 0;

    watch(
        () => toValue(resourceId),
        (id) => void loadDescription(id),
        { immediate: true },
    );

    async function loadDescription(id: string): Promise<void> {
        const requestId = ++latestRequestId;
        description.value = "";
        canEdit.value = false;
        hasFailed.value = false;
        isLoading.value = true;
        try {
            const descriptors = await fetchResourceDescriptors([id], {
                includeCanEdit: true,
            });
            if (requestId !== latestRequestId) return;
            description.value =
                descriptors[id]?.descriptors?.[arches.activeLanguage]
                    ?.description ?? "";
            canEdit.value = descriptors[id]?.can_edit === true;
        } catch {
            if (requestId === latestRequestId) hasFailed.value = true;
        } finally {
            if (requestId === latestRequestId) isLoading.value = false;
        }
    }

    return { description, isLoading, canEdit, hasFailed };
}
