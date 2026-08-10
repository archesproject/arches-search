import { definePreset, palette } from "@primeuix/themes";
import Aura from "@primeuix/themes/aura";

import { compileGlobalCss } from "@/arches_modular_reports/utils.ts";

const archesSearchTeal = "#0d9488";

const cssOverrides = {
    ":root": {
        "--arches-search-radius-pill": "10rem",

        "--arches-search-page-bg": "#f6f7f9",
        "--arches-search-card-bg": "#ffffff",

        "--arches-search-chip-search-bg": "#f1f5f9",
        "--arches-search-chip-search-border": "#cbd5e1",
        "--arches-search-chip-search-text": "#334155",

        "--arches-search-highlight-bg": "#e0f2fe",
        "--arches-search-highlight-text": "#0369a1",

        "--arches-search-live-bg": "#dcfce7",
        "--arches-search-live-text": "#15803d",

        "--arches-search-filter-resource-type-bg": "#ccfbf1",
        "--arches-search-filter-resource-type-border": "#5eead4",
        "--arches-search-filter-resource-type-text": "#0f766e",

        "--arches-search-filter-time-bg": "#fef3c7",
        "--arches-search-filter-time-border": "#fcd34d",
        "--arches-search-filter-time-text": "#92400e",

        "--arches-search-filter-map-bg": "#eff6ff",
        "--arches-search-filter-map-border": "#93c5fd",
        "--arches-search-filter-map-text": "#1d4ed8",

        "--arches-search-filter-attribute-bg": "#f5f3ff",
        "--arches-search-filter-attribute-border": "#c4b5fd",
        "--arches-search-filter-attribute-text": "#5b21b6",

        "--arches-search-filter-controlled-term-bg": "#f5f3ff",
        "--arches-search-filter-controlled-term-border": "#c4b5fd",
        "--arches-search-filter-controlled-term-text": "#5b21b6",

        "--arches-search-filter-record-bg": "#f0fdf4",
        "--arches-search-filter-record-border": "#86efac",
        "--arches-search-filter-record-text": "#15803d",

        "--arches-search-sec-btn-hover-bg": "#e2e8f0",
        "--arches-search-sec-btn-text": "#475569",
        "--arches-search-chip-border": "#cbd5e1",
    },
    ".p-theme-dark": {
        "--arches-search-page-bg": "#0a0a0a",
        "--arches-search-card-bg": "#171717",

        "--arches-search-chip-search-bg": "#262626",
        "--arches-search-chip-search-border": "#404040",
        "--arches-search-chip-search-text": "#d4d4d4",

        "--arches-search-highlight-bg": "#082f49",
        "--arches-search-highlight-text": "#7dd3fc",

        "--arches-search-live-bg": "#052e16",
        "--arches-search-live-text": "#4ade80",

        "--arches-search-filter-resource-type-bg": "#042f2e",
        "--arches-search-filter-resource-type-border": "#0d9488",
        "--arches-search-filter-resource-type-text": "#34d399",

        "--arches-search-filter-time-bg": "#2d1f07",
        "--arches-search-filter-time-border": "#a16207",
        "--arches-search-filter-time-text": "#fde68a",

        "--arches-search-filter-map-bg": "#082030",
        "--arches-search-filter-map-border": "#1d4ed8",
        "--arches-search-filter-map-text": "#93c5fd",

        "--arches-search-filter-attribute-bg": "#2d1049",
        "--arches-search-filter-attribute-border": "#7c3aed",
        "--arches-search-filter-attribute-text": "#c4b5fd",

        "--arches-search-filter-controlled-term-bg": "#2d1049",
        "--arches-search-filter-controlled-term-border": "#7c3aed",
        "--arches-search-filter-controlled-term-text": "#c4b5fd",

        "--arches-search-filter-record-bg": "#052e16",
        "--arches-search-filter-record-border": "#16a34a",
        "--arches-search-filter-record-text": "#4ade80",

        "--arches-search-sec-btn-hover-bg": "#404040",

        "--arches-search-sec-btn-text": "#a3a3a3",

        "--arches-search-chip-border": "#262626",
    },
};

// TODO: when dropping support for 7.6, just import from arches 8.
const DEFAULT_THEME = {
    theme: {
        // preset: ArchesPreset,
        options: {
            prefix: "p",
            darkModeSelector: ".p-theme-dark",
            // darkModeSelector: ":root",
            cssLayer: false,
        },
    },
};

// TODO: when dropping support for 7.6, extend ArchesPreset.
const ArchesSearchPreset = definePreset(Aura, {
    extend: {
        archesSearch: {
            fontSize: "1.6rem",
        },
    },
    semantic: {
        primary: palette(archesSearchTeal),
    },
    css: compileGlobalCss(cssOverrides),
    components: {},
});

export default {
    theme: {
        ...DEFAULT_THEME.theme,
        preset: ArchesSearchPreset,
    },
};
