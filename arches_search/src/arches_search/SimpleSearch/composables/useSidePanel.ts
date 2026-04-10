import { computed, onUnmounted, ref } from "vue";
import type { CSSProperties } from "vue";

const SIDE_PANEL_SIZE = 40;
const SIDE_PANEL_MIN_SIZE = 15;
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
    const sidePanelBasis = ref(SIDE_PANEL_SIZE);
    const isSplitterResizing = ref(false);

    let switchTimer: ReturnType<typeof setTimeout> | null = null;

    const hasOpenSidePanel = computed<boolean>(
        () => isSidePanelOpen.value && activeSidePanel.value !== null,
    );

    const isAttributeFiltersOpen = computed<boolean>(
        () =>
            hasOpenSidePanel.value &&
            activeSidePanel.value === ATTRIBUTE_FILTERS_PANEL,
    );

    const isTimeFilterOpen = computed<boolean>(
        () =>
            hasOpenSidePanel.value &&
            activeSidePanel.value === TIME_FILTER_PANEL,
    );

    // Stay true during the close animation so the panel component stays mounted.
    const isAttributeFiltersActive = computed<boolean>(
        () => activeSidePanel.value === ATTRIBUTE_FILTERS_PANEL,
    );

    const isTimeFilterActive = computed<boolean>(
        () => activeSidePanel.value === TIME_FILTER_PANEL,
    );

    const resultsPanelSize = computed<number>(
        () => 100 - (hasOpenSidePanel.value ? sidePanelBasis.value : 0),
    );

    const visibleSidePanelSize = computed<number>(() =>
        hasOpenSidePanel.value ? sidePanelBasis.value : 0,
    );

    const sidePanelMinSize = computed<number>(() =>
        hasOpenSidePanel.value ? SIDE_PANEL_MIN_SIZE : 0,
    );

    const splitterStateClass = computed<string>(() =>
        hasOpenSidePanel.value ? "side-panel-open" : "side-panel-closed",
    );

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
        const isOpen = hasOpenSidePanel.value;
        const panelSize = isOpen ? `${sidePanelBasis.value}%` : "0";
        return {
            flexGrow: "0",
            flexShrink: "0",
            flexBasis: panelSize,
            maxWidth: panelSize,
            minWidth: "0",
            borderInlineStartColor: isOpen
                ? "var(--p-content-border-color)"
                : "transparent",
            transition: sidePanelTransition.value,
            pointerEvents: isOpen ? "auto" : "none",
        };
    });

    function clearSwitchTimer(): void {
        if (switchTimer !== null) {
            clearTimeout(switchTimer);
            switchTimer = null;
        }
    }

    function closeSidePanel(nextPanel: SidePanelType | null = null): void {
        clearSwitchTimer();

        if (!hasOpenSidePanel.value) {
            activeSidePanel.value = nextPanel;
            isSidePanelOpen.value = nextPanel !== null;
            return;
        }

        isSidePanelOpen.value = false;
        switchTimer = setTimeout(() => {
            activeSidePanel.value = nextPanel;
            isSidePanelOpen.value = nextPanel !== null;
            switchTimer = null;
        }, SIDE_PANEL_SWITCH_DELAY_MS);
    }

    function openSidePanel(panelType: SidePanelType): void {
        clearSwitchTimer();
        activeSidePanel.value = panelType;
        isSidePanelOpen.value = true;
    }

    function toggleSidePanel(panelType: SidePanelType): void {
        if (hasOpenSidePanel.value) {
            const next = activeSidePanel.value === panelType ? null : panelType;
            closeSidePanel(next);
            return;
        }
        openSidePanel(panelType);
    }

    function onSplitterResize(event: SplitterResizeEvent): void {
        const size = event.sizes?.[1];
        if (hasOpenSidePanel.value && typeof size === "number" && size > 0) {
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

    onUnmounted(clearSwitchTimer);

    return {
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
