import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ExportResultsPanel from "@/arches_search/SimpleSearch/components/ExportResultsPanel.vue";

import { fetchExportFormats } from "@/arches_search/SimpleSearch/api.ts";

import type { ExportFormat } from "@/arches_search/SimpleSearch/types.ts";

vi.mock("@/arches_search/SimpleSearch/api.ts", () => ({
    fetchExportFormats: vi.fn(),
}));

// Stand-ins for the UI library's components. The radio button selects its
// value when clicked, which is all the panel relies on.
vi.mock("openvue/radiobutton", () => ({
    default: {
        name: "RadioButtonStub",
        props: {
            modelValue: { type: String, default: null },
            value: { type: String, default: "" },
            inputId: { type: String, default: "" },
        },
        emits: ["update:modelValue"],
        template:
            "<input type='radio' :id='inputId' :checked='modelValue === value' @click=\"$emit('update:modelValue', value)\" />",
    },
}));

vi.mock("openvue/inputtext", () => ({
    default: {
        name: "InputTextStub",
        template: "<input type='text' />",
    },
}));

vi.mock("openvue/button", () => ({
    default: {
        name: "ButtonStub",
        props: {
            label: { type: String, default: "" },
            disabled: { type: Boolean, default: false },
        },
        emits: ["click"],
        template:
            "<button type='button' :disabled='disabled' @click=\"$emit('click')\">{{ label }}</button>",
    },
}));

const BRANCH_EXCEL: ExportFormat = {
    slug: "branch-excel-exporter",
    name: "Branch Excel Exporter",
    description: "Export branch data",
    offersExportConceptsAs: false,
};
const TILE_EXCEL: ExportFormat = {
    slug: "tile-excel-exporter",
    name: "Tile Excel Exporter",
    description: "Export tile data",
    offersExportConceptsAs: true,
};

async function mountPanel(hasSingleGraph = true) {
    const wrapper = mount(ExportResultsPanel, {
        props: { hasSingleGraph, resultCount: 5 },
    });
    await flushPromises();
    return wrapper;
}

function exportButton(wrapper: Awaited<ReturnType<typeof mountPanel>>) {
    return wrapper
        .findAll("button")
        .find((button) => button.text() === "Export")!;
}

describe("ExportResultsPanel formats", () => {
    beforeEach(() => {
        vi.mocked(fetchExportFormats).mockReset();
    });

    it("lists every format the server makes available", async () => {
        vi.mocked(fetchExportFormats).mockResolvedValue([
            BRANCH_EXCEL,
            TILE_EXCEL,
        ]);
        const wrapper = await mountPanel();

        const names = wrapper
            .findAll(".format-option-name")
            .map((name) => name.text());
        expect(names).toEqual([BRANCH_EXCEL.name, TILE_EXCEL.name]);
        expect(wrapper.text()).toContain(TILE_EXCEL.description);
    });

    it("shows a message when no formats are available", async () => {
        vi.mocked(fetchExportFormats).mockResolvedValue([]);
        const wrapper = await mountPanel();

        expect(wrapper.find(".format-status").text()).toBe(
            "No export formats are available to you.",
        );
        expect(exportButton(wrapper).attributes("disabled")).toBeDefined();
    });

    it("shows a message when the formats cannot be loaded", async () => {
        vi.mocked(fetchExportFormats).mockRejectedValue(new Error("boom"));
        const wrapper = await mountPanel();

        expect(wrapper.find(".format-status").text()).toBe(
            "Export formats could not be loaded.",
        );
        expect(exportButton(wrapper).attributes("disabled")).toBeDefined();
    });

    it("emits the selected format's slug on export", async () => {
        vi.mocked(fetchExportFormats).mockResolvedValue([
            BRANCH_EXCEL,
            TILE_EXCEL,
        ]);
        const wrapper = await mountPanel();

        await wrapper
            .find(`#export-format-${TILE_EXCEL.slug}`)
            .trigger("click");
        await exportButton(wrapper).trigger("click");

        expect(wrapper.emitted("export")).toEqual([
            [
                {
                    format: TILE_EXCEL.slug,
                    filename: "search_export",
                    exportConceptsAs: "labels",
                },
            ],
        ]);
    });
});

describe("ExportResultsPanel concepts", () => {
    beforeEach(() => {
        vi.mocked(fetchExportFormats).mockReset();
        vi.mocked(fetchExportFormats).mockResolvedValue([
            BRANCH_EXCEL,
            TILE_EXCEL,
        ]);
    });

    it("hides the choice for a format that does not offer it", async () => {
        const wrapper = await mountPanel();

        expect(wrapper.find("#export-concepts-labels").exists()).toBe(false);
    });

    it("offers the choice for a format that does", async () => {
        const wrapper = await mountPanel();

        await wrapper
            .find(`#export-format-${TILE_EXCEL.slug}`)
            .trigger("click");

        expect(wrapper.find("#export-concepts-labels").exists()).toBe(true);
        expect(wrapper.find("#export-concepts-uuids").exists()).toBe(true);
    });

    it("emits the chosen way of exporting concepts", async () => {
        const wrapper = await mountPanel();

        await wrapper
            .find(`#export-format-${TILE_EXCEL.slug}`)
            .trigger("click");
        await wrapper.find("#export-concepts-uuids").trigger("click");
        await exportButton(wrapper).trigger("click");

        expect(wrapper.emitted("export")).toEqual([
            [
                {
                    format: TILE_EXCEL.slug,
                    filename: "search_export",
                    exportConceptsAs: "uuids",
                },
            ],
        ]);
    });
});
