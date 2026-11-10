import { computed, onWatcherCleanup, watch } from "vue";

import { fetchResourceDescriptor } from "@/arches_vue_components/components/MapComponent/api.ts";
import { FIT_TO_FEATURES_PADDING } from "@/arches_vue_components/components/MapComponent/constants.ts";
import { useResultsMapSelection } from "@/arches_search/SimpleSearch/composables/useResultsMapSelection.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";
import { SEARCH_RESULTS_SOURCE } from "@/arches_search/SimpleSearch/types.ts";
import { boundsOfGeometries } from "@/arches_search/SimpleSearch/utils/geometry-bounds.ts";

import type { Ref, ShallowRef } from "vue";
import type { Feature } from "geojson";
import type { Map as MaplibreMap } from "maplibre-gl";
import type MapComponent from "@/arches_vue_components/components/MapComponent/MapComponent.vue";
import type { ResultsMapFocusRequest } from "@/arches_search/SimpleSearch/composables/useResultsMapSelection.ts";

const MAP_SIZE_SETTLE_DELAY_MS = 150;
const SHOW_ON_MAP_MAX_ZOOM = 14;

export function useResultsMapFocus(
    mapComponentRef: Readonly<
        ShallowRef<InstanceType<typeof MapComponent> | null>
    >,
    isMapReady: Readonly<Ref<boolean>>,
): void {
    const resultsMapSelection = useResultsMapSelection();
    const { resultsTileUrl } = useSearchFilters();

    const popupFeature = computed<Feature | null>(
        () => mapComponentRef.value?.context.popupFeature.value ?? null,
    );

    const popupSearchResultId = computed<string | null>(() => {
        const feature = popupFeature.value;
        if (
            feature !== null &&
            "source" in feature &&
            feature.source === SEARCH_RESULTS_SOURCE
        ) {
            return feature.properties?.resourceinstanceid ?? null;
        }
        return null;
    });

    watch(
        () => resultsMapSelection?.focusRequest.value ?? null,
        (focusRequest) => {
            if (focusRequest === null) {
                return;
            }
            const abortController = new AbortController();
            onWatcherCleanup(() => {
                abortController.abort();
            });
            void focusResource(focusRequest, abortController.signal);
        },
    );

    watch(resultsTileUrl, clearSelection);

    watch(popupFeature, syncPinWithPopup);

    watch(
        () => resultsMapSelection?.pinnedResourceId.value ?? null,
        (pinnedResourceId) => {
            if (
                pinnedResourceId === null &&
                popupSearchResultId.value !== null
            ) {
                mapComponentRef.value?.context.closeFeaturePopup();
            }
        },
    );

    function syncPinWithPopup(): void {
        if (!resultsMapSelection) {
            return;
        }

        const searchResultId = popupSearchResultId.value;
        if (searchResultId !== null) {
            resultsMapSelection.selectedResourceId.value = searchResultId;
            resultsMapSelection.pinnedResourceId.value = searchResultId;
            return;
        }

        if (popupFeature.value !== null) {
            resultsMapSelection.selectedResourceId.value = null;
        }
        resultsMapSelection.unpin();
    }

    async function focusResource(
        focusRequest: ResultsMapFocusRequest,
        abortSignal: AbortSignal,
    ): Promise<void> {
        try {
            await waitForMapReady(abortSignal);
            const map = mapComponentRef.value?.map;
            const context = mapComponentRef.value?.context;
            if (!map || !context || abortSignal.aborted) {
                return;
            }

            const didMapResize = await waitForMapSizeToSettle(map, abortSignal);
            if (abortSignal.aborted) {
                return;
            }

            const descriptor = await fetchResourceDescriptor(
                focusRequest.resourceId,
                abortSignal,
            );
            if (abortSignal.aborted) {
                return;
            }

            const geometries = descriptor.geometries.flatMap(
                (descriptorGeometry) =>
                    descriptorGeometry.geom.features.map(
                        (feature) => feature.geometry,
                    ),
            );
            const bounds = boundsOfGeometries(geometries);

            if (popupSearchResultId.value !== focusRequest.resourceId) {
                context.closeFeaturePopup();
            }
            if (bounds !== null) {
                map.fitBounds(bounds, {
                    padding: FIT_TO_FEATURES_PADDING,
                    maxZoom: SHOW_ON_MAP_MAX_ZOOM,
                    animate: !didMapResize,
                });
            }
            context.showFeatureHighlight(geometries);
        } catch (error) {
            if (!abortSignal.aborted) {
                console.error("Failed to show the resource on the map:", error);
            }
        }
    }

    function clearSelection(): void {
        if (resultsMapSelection) {
            resultsMapSelection.focusRequest.value = null;
            resultsMapSelection.selectedResourceId.value = null;
        }
        mapComponentRef.value?.context.closeFeaturePopup();
        mapComponentRef.value?.context.clearFeatureHighlight();
    }

    function waitForMapReady(abortSignal: AbortSignal): Promise<void> {
        if (isMapReady.value) {
            return Promise.resolve();
        }
        return new Promise((resolve) => {
            const stopWatching = watch(isMapReady, (ready) => {
                if (ready) {
                    finish();
                }
            });

            function finish(): void {
                stopWatching();
                resolve();
            }

            abortSignal.addEventListener("abort", finish, { once: true });
        });
    }

    function waitForMapSizeToSettle(
        map: MaplibreMap,
        abortSignal: AbortSignal,
    ): Promise<boolean> {
        return new Promise((resolve) => {
            let settleTimeout: ReturnType<typeof setTimeout> | undefined;
            let didMapResize = false;

            function restartSettleTimer(): void {
                clearTimeout(settleTimeout);
                settleTimeout = setTimeout(
                    finishOnceVisible,
                    MAP_SIZE_SETTLE_DELAY_MS,
                );
            }

            function onMapResize(): void {
                didMapResize = true;
                restartSettleTimer();
            }

            function finishOnceVisible(): void {
                const { width, height } = map
                    .getContainer()
                    .getBoundingClientRect();
                if (width > 0 && height > 0) {
                    finish();
                }
            }

            function finish(): void {
                clearTimeout(settleTimeout);
                map.off("resize", onMapResize);
                resolve(didMapResize);
            }

            map.on("resize", onMapResize);
            abortSignal.addEventListener("abort", finish, { once: true });
            restartSettleTimer();
        });
    }
}
