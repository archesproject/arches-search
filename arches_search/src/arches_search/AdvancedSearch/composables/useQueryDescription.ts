import { computed, onScopeDispose, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import {
    getNodeMetadataForPayload,
    getResourceNamesForPayload,
} from "@/arches_search/AdvancedSearch/api.ts";
import { describeAdvancedSearchQuery } from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/components/NarrationPanel/query-narrator.ts";
import { toError } from "@/arches_search/AdvancedSearch/utils/errors.ts";

import type { ComputedRef, Ref } from "vue";
import type {
    AdvancedSearchFacet,
    GraphModel,
    GroupPayload,
    NodeMetadataMap,
} from "@/arches_search/AdvancedSearch/types.ts";

// Field labels and resource names are fetched once editing pauses, rather
// than on every keystroke.
const DESCRIPTION_DATA_DEBOUNCE_MS = 400;

export function useQueryDescription({
    payload,
    graphs,
    datatypesToAdvancedSearchFacets,
}: {
    payload: Readonly<Ref<GroupPayload | null>>;
    graphs: Readonly<Ref<GraphModel[]>>;
    datatypesToAdvancedSearchFacets: Readonly<
        Ref<Record<string, AdvancedSearchFacet[]>>
    >;
}): {
    description: ComputedRef<string>;
    isLoading: Ref<boolean>;
    fetchError: Ref<Error | null>;
} {
    const gettext = useGettext();

    const nodeMetadata = ref<NodeMetadataMap>({});
    const resourceNames = ref<Record<string, string>>({});
    const isLoading = ref(false);
    const fetchError = ref<Error | null>(null);

    let fetchTimeout: ReturnType<typeof setTimeout> | null = null;
    let latestRequestNumber = 0;

    const description = computed<string>(() => {
        if (!payload.value) {
            return "";
        }
        return describeAdvancedSearchQuery({
            payload: payload.value,
            graphs: graphs.value,
            datatypesToAdvancedSearchFacets:
                datatypesToAdvancedSearchFacets.value,
            gettext: gettext.$gettext,
            currentLanguage: gettext.current,
            nodeMetadata: nodeMetadata.value,
            resourceNames: resourceNames.value,
        });
    });

    watch(
        payload,
        (currentPayload) => {
            if (fetchTimeout) {
                clearTimeout(fetchTimeout);
            }
            if (!currentPayload) {
                isLoading.value = false;
                return;
            }
            isLoading.value = true;
            fetchTimeout = setTimeout(() => {
                void loadDescriptionData(currentPayload);
            }, DESCRIPTION_DATA_DEBOUNCE_MS);
        },
        { immediate: true },
    );

    onScopeDispose(() => {
        if (fetchTimeout) {
            clearTimeout(fetchTimeout);
        }
    });

    async function loadDescriptionData(
        currentPayload: GroupPayload,
    ): Promise<void> {
        latestRequestNumber += 1;
        const requestNumber = latestRequestNumber;
        fetchError.value = null;

        try {
            const [fetchedMetadata, fetchedResourceNames] = await Promise.all([
                getNodeMetadataForPayload(currentPayload),
                getResourceNamesForPayload(currentPayload),
            ]);
            if (requestNumber !== latestRequestNumber) {
                return;
            }
            nodeMetadata.value = fetchedMetadata ?? {};
            resourceNames.value = fetchedResourceNames ?? {};
        } catch (error) {
            if (requestNumber !== latestRequestNumber) {
                return;
            }
            fetchError.value = toError(error);
        } finally {
            if (requestNumber === latestRequestNumber) {
                isLoading.value = false;
            }
        }
    }

    return { description, isLoading, fetchError };
}
