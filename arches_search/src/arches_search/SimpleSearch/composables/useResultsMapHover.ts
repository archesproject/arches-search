import { computed, watch } from "vue";

import {
    BUFFER_LAYER_ID,
    FEATURE_HIGHLIGHT_LINE_WIDTH,
    FEATURE_HIGHLIGHT_POINT_RADIUS,
} from "@/arches_vue_components/components/MapComponent/constants.ts";
import { useResultsMapSelection } from "@/arches_search/SimpleSearch/composables/useResultsMapSelection.ts";
import {
    SEARCH_RESULTS_SOURCE,
    SEARCH_RESULTS_SOURCE_LAYER,
} from "@/arches_search/SimpleSearch/types.ts";

import type { ShallowRef } from "vue";
import type {
    AddLayerObject,
    DataDrivenPropertyValueSpecification,
    FilterSpecification,
    MapMouseEvent,
} from "maplibre-gl";
import type MapComponent from "@/arches_vue_components/components/MapComponent/MapComponent.vue";
import type { MapLayer } from "@/arches_vue_components/components/MapComponent/types.ts";

const HOVER_RING_COLOR = "#ffffff";
const HOVER_RING_EDGE_COLOR = "#1f2933";
const HOVER_RING_EDGE_WIDTH = 1;
const TRANSPARENT_COLOR = "rgba(0, 0, 0, 0)";
const HOVER_FEATURE_STATE = "hover";
const VISIBLE = "visible" as const;
const HIDDEN = "none" as const;
const POINT_GEOMETRY_TYPES = ["Point", "MultiPoint"];

const HOVER_POINT_EDGE_LAYER_ID = "arches-search-results-hover-point-edge";
const HOVER_POINT_RING_LAYER_ID = "arches-search-results-hover-point-ring";
const HOVER_LINE_EDGE_LAYER_ID = "arches-search-results-hover-line-edge";
const HOVER_LINE_LAYER_ID = "arches-search-results-hover-line";

const POINT_FILTER: FilterSpecification = [
    "in",
    ["geometry-type"],
    ["literal", POINT_GEOMETRY_TYPES],
];
const NON_POINT_FILTER: FilterSpecification = ["!", POINT_FILTER];
const HOVERED_OPACITY: DataDrivenPropertyValueSpecification<number> = [
    "case",
    ["boolean", ["feature-state", HOVER_FEATURE_STATE], false],
    1,
    0,
];

export function useResultsMapHover(
    mapComponentRef: Readonly<
        ShallowRef<InstanceType<typeof MapComponent> | null>
    >,
): {
    addResultsHoverLayers: () => void;
    listenForResultsHover: () => void;
} {
    const resultsMapSelection = useResultsMapSelection();

    const ringedResourceId = computed<string | null>(() => {
        const currentlyHoveredResourceId =
            resultsMapSelection?.hoveredResourceId.value ?? null;
        if (
            currentlyHoveredResourceId ===
            resultsMapSelection?.selectedResourceId.value
        ) {
            return null;
        }
        return currentlyHoveredResourceId;
    });

    const resultsOverlay = computed<MapLayer | null>(
        () =>
            mapComponentRef.value?.context.overlays.value.find((overlay) =>
                overlay.layerdefinitions.some(
                    (layerDefinition) =>
                        layerDefinition.source === SEARCH_RESULTS_SOURCE,
                ),
            ) ?? null,
    );

    const isResultsOverlayShown = computed<boolean>(
        () => resultsOverlay.value?.addtomap === true,
    );

    watch(ringedResourceId, (currentResourceId, previousResourceId) => {
        setResourceHoverState(previousResourceId, false);
        setResourceHoverState(currentResourceId, true);
    });
    watch(isResultsOverlayShown, addResultsHoverLayers, { flush: "post" });

    function addResultsHoverLayers(): void {
        const map = mapComponentRef.value?.map;
        if (!map || !map.getSource(SEARCH_RESULTS_SOURCE)) {
            return;
        }

        let beforeLayerId: string | undefined;
        if (map.getLayer(BUFFER_LAYER_ID)) {
            beforeLayerId = BUFFER_LAYER_ID;
        }

        let visibility: typeof VISIBLE | typeof HIDDEN = HIDDEN;
        if (isResultsOverlayShown.value) {
            visibility = VISIBLE;
        }

        for (const hoverLayer of buildHoverLayers()) {
            if (!map.getLayer(hoverLayer.id)) {
                map.addLayer(hoverLayer, beforeLayerId);
            }
            map.setLayoutProperty(hoverLayer.id, "visibility", visibility);
        }
    }

    function listenForResultsHover(): void {
        const map = mapComponentRef.value?.map;
        if (!map) {
            return;
        }

        map.on("mousemove", onMapMouseMove);
        map.on("mouseout", onMapMouseOut);
    }

    function onMapMouseMove(event: MapMouseEvent): void {
        if (!resultsMapSelection) {
            return;
        }

        const renderedResultLayerIds = (
            resultsOverlay.value?.layerdefinitions ?? []
        )
            .map((layerDefinition) => layerDefinition.id)
            .filter((layerId) => event.target.getLayer(layerId) !== undefined);

        if (renderedResultLayerIds.length === 0) {
            resultsMapSelection.hoveredResourceId.value = null;
            return;
        }

        const [featureUnderPointer] = event.target.queryRenderedFeatures(
            event.point,
            { layers: renderedResultLayerIds },
        );
        if (
            featureUnderPointer === undefined ||
            mapComponentRef.value?.context.isFeatureClickBlockedByDrawing(
                event.point,
            ) === true
        ) {
            resultsMapSelection.hoveredResourceId.value = null;
            return;
        }
        resultsMapSelection.hoveredResourceId.value =
            featureUnderPointer.properties.resourceinstanceid ?? null;
    }

    function onMapMouseOut(): void {
        if (resultsMapSelection) {
            resultsMapSelection.hoveredResourceId.value = null;
        }
    }

    function setResourceHoverState(
        resourceId: string | null,
        isHovered: boolean,
    ): void {
        const map = mapComponentRef.value?.map;
        if (resourceId === null || !map?.getSource(SEARCH_RESULTS_SOURCE)) {
            return;
        }

        map.setFeatureState(
            {
                source: SEARCH_RESULTS_SOURCE,
                sourceLayer: SEARCH_RESULTS_SOURCE_LAYER,
                id: resourceId,
            },
            { [HOVER_FEATURE_STATE]: isHovered },
        );
    }

    function buildHoverLayers(): AddLayerObject[] {
        return [
            {
                id: HOVER_POINT_EDGE_LAYER_ID,
                type: "circle",
                source: SEARCH_RESULTS_SOURCE,
                "source-layer": SEARCH_RESULTS_SOURCE_LAYER,
                filter: POINT_FILTER,
                paint: {
                    "circle-radius":
                        FEATURE_HIGHLIGHT_POINT_RADIUS - HOVER_RING_EDGE_WIDTH,
                    "circle-color": TRANSPARENT_COLOR,
                    "circle-stroke-color": HOVER_RING_EDGE_COLOR,
                    "circle-stroke-width":
                        FEATURE_HIGHLIGHT_LINE_WIDTH +
                        2 * HOVER_RING_EDGE_WIDTH,
                    "circle-stroke-opacity": HOVERED_OPACITY,
                },
            },
            {
                id: HOVER_POINT_RING_LAYER_ID,
                type: "circle",
                source: SEARCH_RESULTS_SOURCE,
                "source-layer": SEARCH_RESULTS_SOURCE_LAYER,
                filter: POINT_FILTER,
                paint: {
                    "circle-radius": FEATURE_HIGHLIGHT_POINT_RADIUS,
                    "circle-color": TRANSPARENT_COLOR,
                    "circle-stroke-color": HOVER_RING_COLOR,
                    "circle-stroke-width": FEATURE_HIGHLIGHT_LINE_WIDTH,
                    "circle-stroke-opacity": HOVERED_OPACITY,
                },
            },
            {
                id: HOVER_LINE_EDGE_LAYER_ID,
                type: "line",
                source: SEARCH_RESULTS_SOURCE,
                "source-layer": SEARCH_RESULTS_SOURCE_LAYER,
                filter: NON_POINT_FILTER,
                layout: { "line-cap": "round", "line-join": "round" },
                paint: {
                    "line-color": HOVER_RING_EDGE_COLOR,
                    "line-width":
                        FEATURE_HIGHLIGHT_LINE_WIDTH +
                        2 * HOVER_RING_EDGE_WIDTH,
                    "line-opacity": HOVERED_OPACITY,
                },
            },
            {
                id: HOVER_LINE_LAYER_ID,
                type: "line",
                source: SEARCH_RESULTS_SOURCE,
                "source-layer": SEARCH_RESULTS_SOURCE_LAYER,
                filter: NON_POINT_FILTER,
                layout: { "line-cap": "round", "line-join": "round" },
                paint: {
                    "line-color": HOVER_RING_COLOR,
                    "line-width": FEATURE_HIGHLIGHT_LINE_WIDTH,
                    "line-opacity": HOVERED_OPACITY,
                },
            },
        ];
    }

    return { addResultsHoverLayers, listenForResultsHover };
}
