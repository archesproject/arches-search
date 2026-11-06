import { computed, onScopeDispose, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import {
    getNodeMetadataForPayload,
    getResourceNamesForPayload,
} from "@/arches_search/AdvancedSearch/api.ts";
import { describeAdvancedSearchQuery } from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/components/NarrationPanel/query-narrator.ts";

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
    isLoading: ComputedRef<boolean>;
    fetchError: ComputedRef<Error | null>;
} {
    const gettext = useGettext();

    const nodeMetadata = ref<NodeMetadataMap>({});
    const resourceNames = ref<Record<string, string>>({});
    const loadErrorByPayloadKey = ref<Record<string, Error | null>>({});

    let fetchTimeout: ReturnType<typeof setTimeout> | null = null;

    const payloadKey = computed<string | null>(() => {
        if (!payload.value) {
            return null;
        }
        return JSON.stringify(payload.value);
    });

    const isLoading = computed<boolean>(
        () =>
            payloadKey.value !== null &&
            !(payloadKey.value in loadErrorByPayloadKey.value),
    );

    const fetchError = computed<Error | null>(() => {
        if (!payloadKey.value) {
            return null;
        }
        return loadErrorByPayloadKey.value[payloadKey.value] ?? null;
    });

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
        payloadKey,
        (currentPayloadKey) => {
            if (fetchTimeout) {
                clearTimeout(fetchTimeout);
            }
            const currentPayload = payload.value;
            if (!currentPayloadKey || !currentPayload) {
                return;
            }
            fetchTimeout = setTimeout(() => {
                void loadDescriptionData(currentPayloadKey, currentPayload);
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
        currentPayloadKey: string,
        currentPayload: GroupPayload,
    ): Promise<void> {
        let loadError: Error | null = null;
        try {
            const [fetchedMetadata, fetchedResourceNames] = await Promise.all([
                getNodeMetadataForPayload(currentPayload),
                getResourceNamesForPayload(currentPayload),
            ]);
            nodeMetadata.value = { ...nodeMetadata.value, ...fetchedMetadata };
            resourceNames.value = {
                ...resourceNames.value,
                ...fetchedResourceNames,
            };
        } catch (error) {
            loadError = error as Error;
        }
        loadErrorByPayloadKey.value = {
            ...loadErrorByPayloadKey.value,
            [currentPayloadKey]: loadError,
        };
    }

    return { description, isLoading, fetchError };
}
