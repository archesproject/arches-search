import { defineComponent } from "vue";
import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useSidePanel } from "@/arches_search/SimpleSearch/composables/useSidePanel.ts";

function mountPanel() {
    let panel: ReturnType<typeof useSidePanel> | undefined;
    const wrapper = mount(
        defineComponent({
            setup() {
                panel = useSidePanel();
                return {};
            },
            render() {
                return null;
            },
        }),
    );
    if (!panel) throw new Error("Panel did not initialize");
    return { panel, wrapper };
}

describe("side panel transitions", () => {
    beforeEach(() => vi.useFakeTimers());
    afterEach(() => vi.useRealTimers());

    it("restores visibility when reopening during a close transition", () => {
        const { panel, wrapper } = mountPanel();
        panel.openAttributeFilters();
        vi.runAllTimers();
        expect(panel.isAttributeFiltersOpen.value).toBe(true);

        panel.closeSidePanel();
        expect(
            panel.sidePanelContentClass.value["side-panel-content-open"],
        ).toBe(false);
        panel.openAttributeFilters();
        expect(
            panel.sidePanelContentClass.value["side-panel-content-open"],
        ).toBe(true);
        vi.runAllTimers();
        expect(panel.isAttributeFiltersOpen.value).toBe(true);
        wrapper.unmount();
    });

    it("keeps normal switches and closes working", () => {
        const { panel, wrapper } = mountPanel();
        panel.openMapFilter();
        vi.runAllTimers();
        expect(panel.isMapFilterOpen.value).toBe(true);
        panel.closeSidePanel();
        vi.runAllTimers();
        expect(panel.isIdle.value).toBe(true);
        expect(
            panel.sidePanelContentClass.value["side-panel-content-open"],
        ).toBe(true);
        wrapper.unmount();
    });
});
