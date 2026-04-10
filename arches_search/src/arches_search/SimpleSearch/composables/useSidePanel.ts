import { computed, onUnmounted, ref } from "vue";
import type { CSSProperties } from "vue";

const TOTAL_PANEL_SIZE = 100;
const SIDE_PANEL_SIZE = 40;
const SIDE_PANEL_MIN_SIZE = 15;
const PANEL_COLLAPSED_SIZE = "0" as const;
const FLEX_TRANSITION = "240ms ease" as const;
const BORDER_TRANSITION = "180ms ease" as const;
const SIDE_PANEL_SWITCH_DELAY_MS = 240;
const ATTRIBUTE_FILTERS_PANEL = "attribute-filters" as const;
const TIME_FILTER_PANEL = "time-filter" as const;

interface SplitterResizeEvent {
    sizes?: number[];
}

type SidePanelType = typeof ATTRIBUTE_FILTERS_PANEL | typeof TIME_FILTER_PANEL;

export function useSidePanel() {
    const activeSidePanel = ref<SidePanelType | null>(null);
    const isSidePanelOpen = ref(false);
    const sidePanelBasis = ref<number>(SIDE_PANEL_SIZE);
    const isSplitterResizing = ref(false);

    let sidePanelSwitchTimer: ReturnType<typeof setTimeout> | null = null;

    const hasOpenSidePanel = computed<boolean>(() => {
        return isSidePanelOpen.value && activeSidePanel.value !== null;
    });

    const isAttributeFiltersOpen = computed<boolean>(() => {
        return (
            hasOpenSidePanel.value &&
            activeSidePanel.value === ATTRIBUTE_FILTERS_PANEL
        );
    });

    const isTimeFilterOpen = computed<boolean>(() => {
        return (
            hasOpenSidePanel.value &&
            activeSidePanel.value === TIME_FILTER_PANEL
        );
    });

    // These differ from isXOpen: they stay true during the close animation so
    // the panel component remains mounted until the transition finishes.
    const isAttributeFiltersActive = computed<boolean>(() => {
        return activeSidePanel.value === ATTRIBUTE_FILTERS_PANEL;
    });

    const isTimeFilterActive = computed<boolean>(() => {
        return activeSidePanel.value === TIME_FILTER_PANEL;
    });

    const resultsPanelSize = computed<number>(() => {
        if (!hasOpenSidePanel.value) {
            return TOTAL_PANEL_SIZE;
        }
        return TOTAL_PANEL_SIZE - sidePanelBasis.value;
    });

    const visibleSidePanelSize = computed<number>(() => {
        return hasOpenSidePanel.value ? sidePanelBasis.value : 0;
    });

    const sidePanelMinSize = computed<number>(() => {
        return hasOpenSidePanel.value ? SIDE_PANEL_MIN_SIZE : 0;
    });

    const splitterStateClass = computed<string>(() => {
        return hasOpenSidePanel.value ? "side-panel-open" : "side-panel-closed";
    });

    const sidePanelContentClass = computed<Record<string, boolean>>(() => ({
        "side-panel-content-open": hasOpenSidePanel.value,
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
        const panelSize = hasOpenSidePanel.value
            ? `${sidePanelBasis.value}%`
            : PANEL_COLLAPSED_SIZE;
        return {
            flexGrow: "0",
            flexShrink: "0",
            flexBasis: panelSize,
            maxWidth: panelSize,
            minWidth: "0",
            borderInlineStartColor: hasOpenSidePanel.value
                ? "var(--p-content-border-color)"
                : "transparent",
            transition: sidePanelTransition.value,
            pointerEvents: hasOpenSidePanel.value ? "auto" : "none",
        };
    });

    function clearSidePanelSwitchTimer(): void {
        if (sidePanelSwitchTimer !== null) {
            clearTimeout(sidePanelSwitchTimer);
            sidePanelSwitchTimer = null;
        }
    }

    function closeSidePanel(nextPanel: SidePanelType | null = null): void {
        clearSidePanelSwitchTimer();

        if (!hasOpenSidePanel.value) {
            activeSidePanel.value = nextPanel;
            isSidePanelOpen.value = nextPanel !== null;
            return;
        }

        isSidePanelOpen.value = false;
        sidePanelSwitchTimer = setTimeout(() => {
            activeSidePanel.value = nextPanel;
            isSidePanelOpen.value = nextPanel !== null;
            sidePanelSwitchTimer = null;
        }, SIDE_PANEL_SWITCH_DELAY_MS);
    }

    function openSidePanel(panelType: SidePanelType): void {
        clearSidePanelSwitchTimer();
        activeSidePanel.value = panelType;
        isSidePanelOpen.value = true;
    }

    function toggleSidePanel(panelType: SidePanelType): void {
        if (hasOpenSidePanel.value && activeSidePanel.value === panelType) {
            closeSidePanel();
            return;
        }

        if (hasOpenSidePanel.value) {
            closeSidePanel(panelType);
            return;
        }

        openSidePanel(panelType);
    }

    function syncSidePanelSizeFromEvent(event: SplitterResizeEvent): void {
        const nextSidePanelSize = event.sizes?.[1];

        if (
            hasOpenSidePanel.value &&
            typeof nextSidePanelSize === "number" &&
            nextSidePanelSize > 0
        ) {
            sidePanelBasis.value = nextSidePanelSize;
        }
    }

    function onToggleAttributeFilters(): void {
        toggleSidePanel(ATTRIBUTE_FILTERS_PANEL);
    }

    function onToggleTimeFilter(): void {
        toggleSidePanel(TIME_FILTER_PANEL);
    }

    function onSplitterResizeStart(): void {
        isSplitterResizing.value = true;
    }

    function onSplitterResize(event: SplitterResizeEvent): void {
        syncSidePanelSizeFromEvent(event);
    }

    function onSplitterResizeEnd(event: SplitterResizeEvent): void {
        syncSidePanelSizeFromEvent(event);
        isSplitterResizing.value = false;
    }

    onUnmounted(() => {
        clearSidePanelSwitchTimer();
    });

    return {
        activeSidePanel,
        isAttributeFiltersActive,
        isAttributeFiltersOpen,
        isTimeFilterActive,
        isTimeFilterOpen,
        hasOpenSidePanel,
        resultsPanelSize,
        visibleSidePanelSize,
        sidePanelMinSize,
        splitterStateClass,
        sidePanelContentClass,
        sidePanelStyle,
        closeSidePanel,
        onToggleAttributeFilters,
        onToggleTimeFilter,
        onSplitterResizeStart,
        onSplitterResize,
        onSplitterResizeEnd,
    };
}
