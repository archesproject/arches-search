import { computed, onUnmounted, provide, ref } from "vue";
import type { CSSProperties } from "vue";

const SIDE_PANEL_SIZE = 40;
const IDLE_PANEL_SIZE = 27;
const SIDE_PANEL_MIN_SIZE = 15;
// OpenVue's Splitter (default gutterSize=4, unless overridden via a
// gutter-size prop on <Splitter> — this app doesn't set one) always writes
// flex-basis as `calc(X% - gutterCount * gutterSize px)`, never a bare
// percentage, both on init and on every drag frame. Splitter re-renders
// itself on every mousemove regardless of whether we listen to its "resize"
// event (its own internal prevSize is reactive), which re-evaluates this
// slot and reasserts sidePanelStyle's own flex-basis right after OpenVue's
// write. A bare percentage here loses that fight on every single frame,
// snapping the panel edge a few px back and reading as stutter on a slow
// drag — matching OpenVue's own compensated value exactly makes the
// reassertion a no-op instead. Two panels means exactly one gutter.
const SPLITTER_GUTTER_SIZE_PX = 4;
const FLEX_TRANSITION = "240ms ease" as const;
const BORDER_TRANSITION = "180ms ease" as const;
const SIDE_PANEL_SWITCH_DELAY_MS = 240;
const IDLE_PANEL = "idle" as const;
const ATTRIBUTE_FILTERS_PANEL = "attribute-filters" as const;
const TIME_FILTER_PANEL = "time-filter" as const;
const MAP_FILTER_PANEL = "map-filter" as const;
const SAVED_SEARCHES_PANEL = "saved-searches" as const;
const EXPORT_RESULTS_PANEL = "export-results" as const;
const RELATED_RESOURCES_PANEL = "related-resources" as const;
const MAX_RELATED_RESOURCES = 2;
const RELATED_RESOURCES_PANEL_SIZE = 35;
const RELATED_RESOURCES_GRAPH_PANEL_SIZE = 65;

interface SplitterResizeEvent {
    sizes?: number[];
}

export interface RelatedResource {
    id: string;
    title: string;
}

type SidePanelType =
    | typeof IDLE_PANEL
    | typeof ATTRIBUTE_FILTERS_PANEL
    | typeof TIME_FILTER_PANEL
    | typeof MAP_FILTER_PANEL
    | typeof SAVED_SEARCHES_PANEL
    | typeof EXPORT_RESULTS_PANEL
    | typeof RELATED_RESOURCES_PANEL;

const PANEL_SIZES: Record<SidePanelType, number> = {
    [IDLE_PANEL]: IDLE_PANEL_SIZE,
    [ATTRIBUTE_FILTERS_PANEL]: 27,
    [TIME_FILTER_PANEL]: SIDE_PANEL_SIZE,
    [MAP_FILTER_PANEL]: 65,
    [SAVED_SEARCHES_PANEL]: 27,
    [EXPORT_RESULTS_PANEL]: 27,
    [RELATED_RESOURCES_PANEL]: RELATED_RESOURCES_PANEL_SIZE,
};

export function useSidePanel() {
    // The side panel always shows *something* — it defaults to the idle
    // "explore your results" tile grid rather than collapsing away, so
    // activeSidePanel is never null.
    const activeSidePanel = ref<SidePanelType>(IDLE_PANEL);
    const sidePanelBasis = ref(PANEL_SIZES[IDLE_PANEL]);
    const isSplitterResizing = ref(false);
    const isSidePanelVisible = ref(true);
    const relatedResources = ref<RelatedResource[]>([]);

    let switchTimer: ReturnType<typeof setTimeout> | null = null;
    // How wide the panel was before the graph widened it, to go back to
    let basisBeforeGraph: number | null = null;
    // How wide it was made, to tell whether the user has resized it since
    let basisWithGraph: number | null = null;

    const isIdle = computed<boolean>(
        () => activeSidePanel.value === IDLE_PANEL,
    );

    const isAttributeFiltersOpen = computed<boolean>(
        () => activeSidePanel.value === ATTRIBUTE_FILTERS_PANEL,
    );

    const isTimeFilterOpen = computed<boolean>(
        () => activeSidePanel.value === TIME_FILTER_PANEL,
    );

    const isMapFilterOpen = computed<boolean>(
        () => activeSidePanel.value === MAP_FILTER_PANEL,
    );

    const isSavedSearchesOpen = computed<boolean>(
        () => activeSidePanel.value === SAVED_SEARCHES_PANEL,
    );

    const isExportResultsOpen = computed<boolean>(
        () => activeSidePanel.value === EXPORT_RESULTS_PANEL,
    );

    const isRelatedResourcesOpen = computed<boolean>(
        () => activeSidePanel.value === RELATED_RESOURCES_PANEL,
    );

    // Kept as separate names for the SimpleSearch.vue v-if chain; identical
    // to the "*Open" computeds now that the panel never fully unmounts.
    const isAttributeFiltersActive = isAttributeFiltersOpen;
    const isTimeFilterActive = isTimeFilterOpen;
    const isMapFilterActive = isMapFilterOpen;
    const isSavedSearchesActive = isSavedSearchesOpen;
    const isExportResultsActive = isExportResultsOpen;

    const resultsPanelSize = computed<number>(() => 100 - sidePanelBasis.value);

    const visibleSidePanelSize = computed<number>(() => sidePanelBasis.value);

    const sidePanelMinSize = computed<number>(() => SIDE_PANEL_MIN_SIZE);

    const sidePanelContentClass = computed<Record<string, boolean>>(() => ({
        "side-panel-content-open": isSidePanelVisible.value,
    }));

    const sidePanelTransition = computed<string>(() => {
        if (isSplitterResizing.value) {
            return `border-inline-start-color ${BORDER_TRANSITION}`;
        }
        return [
            `flex-basis ${FLEX_TRANSITION}`,
            `max-width ${FLEX_TRANSITION}`,
            `border-inline-start-color ${BORDER_TRANSITION}`,
        ].join(", ");
    });

    const sidePanelStyle = computed<CSSProperties>(() => {
        const panelSize = `calc(${sidePanelBasis.value}% - ${SPLITTER_GUTTER_SIZE_PX}px)`;
        return {
            flexGrow: "0",
            flexShrink: "0",
            flexBasis: panelSize,
            maxWidth: panelSize,
            minWidth: "0",
            borderInlineStartColor: "var(--p-content-border-color)",
            transition: sidePanelTransition.value,
            pointerEvents: "auto",
        };
    });

    function clearSwitchTimer(): void {
        if (switchTimer !== null) {
            clearTimeout(switchTimer);
            switchTimer = null;
        }
    }

    function applyPanel(nextPanel: SidePanelType): void {
        if (nextPanel !== RELATED_RESOURCES_PANEL) {
            relatedResources.value = [];
        }
        activeSidePanel.value = nextPanel;
        sidePanelBasis.value = PANEL_SIZES[nextPanel];
        basisBeforeGraph = null;
        basisWithGraph = null;
        isSidePanelVisible.value = true;
    }

    function switchToPanel(nextPanel: SidePanelType): void {
        clearSwitchTimer();

        if (nextPanel === activeSidePanel.value) return;

        isSidePanelVisible.value = false;
        switchTimer = setTimeout(() => {
            applyPanel(nextPanel);
            switchTimer = null;
        }, SIDE_PANEL_SWITCH_DELAY_MS);
    }

    function closeSidePanel(): void {
        switchToPanel(IDLE_PANEL);
    }

    function viewRelatedResource(resource: RelatedResource): void {
        const selected = relatedResources.value;
        if (!selected.some((related) => related.id === resource.id)) {
            // Past the limit the newest resource replaces the last one
            relatedResources.value = [
                ...selected.slice(0, MAX_RELATED_RESOURCES - 1),
                resource,
            ];
        }
        switchToPanel(RELATED_RESOURCES_PANEL);
    }

    // The graph is what needs the room, so the panel widens for it and goes back
    // afterwards. A panel the user has already made wider is left as it is, and
    // so is one the user has resized while the graph was open.
    function setRelatedResourcesGraphVisible(isVisible: boolean): void {
        if (activeSidePanel.value !== RELATED_RESOURCES_PANEL) return;

        if (isVisible) {
            basisBeforeGraph ??= sidePanelBasis.value;
            sidePanelBasis.value = Math.max(
                sidePanelBasis.value,
                RELATED_RESOURCES_GRAPH_PANEL_SIZE,
            );
            basisWithGraph = sidePanelBasis.value;
        } else if (basisBeforeGraph !== null) {
            if (sidePanelBasis.value === basisWithGraph) {
                sidePanelBasis.value = basisBeforeGraph;
            }
            basisBeforeGraph = null;
            basisWithGraph = null;
        }
    }

    function removeRelatedResource(resourceId: string): void {
        relatedResources.value = relatedResources.value.filter(
            (related) => related.id !== resourceId,
        );
        if (relatedResources.value.length === 0) {
            closeSidePanel();
        }
    }

    provide("viewRelatedResource", viewRelatedResource);

    function toggleSidePanel(panelType: SidePanelType): void {
        const next =
            activeSidePanel.value === panelType ? IDLE_PANEL : panelType;
        switchToPanel(next);
    }

    function onSplitterResize(event: SplitterResizeEvent): void {
        const size = event.sizes?.[1];
        if (typeof size === "number" && size > 0) {
            sidePanelBasis.value = size;
        }
    }

    function onSplitterResizeEnd(event: SplitterResizeEvent): void {
        onSplitterResize(event);
        isSplitterResizing.value = false;
    }

    function onSplitterResizeStart(): void {
        isSplitterResizing.value = true;
    }

    function onToggleAttributeFilters(): void {
        toggleSidePanel(ATTRIBUTE_FILTERS_PANEL);
    }

    function onToggleTimeFilter(): void {
        toggleSidePanel(TIME_FILTER_PANEL);
    }

    function onToggleMapFilter(): void {
        toggleSidePanel(MAP_FILTER_PANEL);
    }

    function onToggleSavedSearches(): void {
        toggleSidePanel(SAVED_SEARCHES_PANEL);
    }

    function onToggleExportResults(): void {
        toggleSidePanel(EXPORT_RESULTS_PANEL);
    }

    // Non-toggling opens, distinct from the onToggle* functions above: an
    // active-filter chip's click-to-edit action must always land on its
    // panel, even if that panel is already open — toggling would close it.
    function openAttributeFilters(): void {
        switchToPanel(ATTRIBUTE_FILTERS_PANEL);
    }

    function openTimeFilter(): void {
        switchToPanel(TIME_FILTER_PANEL);
    }

    function openMapFilter(): void {
        switchToPanel(MAP_FILTER_PANEL);
    }

    onUnmounted(clearSwitchTimer);

    return {
        isIdle,
        isAttributeFiltersActive,
        isAttributeFiltersOpen,
        isMapFilterActive,
        isMapFilterOpen,
        isSavedSearchesActive,
        isSavedSearchesOpen,
        isExportResultsActive,
        isExportResultsOpen,
        isTimeFilterActive,
        isTimeFilterOpen,
        isRelatedResourcesOpen,
        relatedResources,
        resultsPanelSize,
        visibleSidePanelSize,
        sidePanelMinSize,
        sidePanelContentClass,
        sidePanelStyle,
        closeSidePanel,
        removeRelatedResource,
        setRelatedResourcesGraphVisible,
        onToggleAttributeFilters,
        onToggleMapFilter,
        onToggleSavedSearches,
        onToggleExportResults,
        onToggleTimeFilter,
        openAttributeFilters,
        openMapFilter,
        openTimeFilter,
        onSplitterResizeStart,
        onSplitterResize,
        onSplitterResizeEnd,
    };
}
