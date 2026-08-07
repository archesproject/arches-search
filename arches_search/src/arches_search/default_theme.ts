import { definePreset, palette } from "@primeuix/themes";
import Aura from "@primeuix/themes/aura";

import { compileGlobalCss } from "@/arches_modular_reports/utils.ts";

const archesSearchTeal = "#0d9488";

// Design tokens with no PrimeVue/Aura equivalent, for concepts this app's
// real (not mocked-up) components actually render today. Neutrals aside
// from the page/card two-tier surface, and the primary color, are handled
// via Aura's own semantic tokens below, so components should prefer those
// (--p-surface-*, --p-text-*, --p-content-*, --p-primary-*) and only reach
// for the custom properties here for one of these specific categories.
const cssOverrides = {
    ":root": {
        "--arches-search-page-bg": "#f6f7f9",
        "--arches-search-card-bg": "#ffffff",

        "--arches-search-chip-search-bg": "#f1f5f9",
        "--arches-search-chip-search-border": "#cbd5e1",
        "--arches-search-chip-search-text": "#334155",

        "--arches-search-highlight-bg": "#e0f2fe",
        "--arches-search-highlight-text": "#0369a1",

        "--arches-search-live-bg": "#dcfce7",
        "--arches-search-live-text": "#15803d",

        // Active-filter chip colors, one per ActiveFilterKind (excluding
        // "term", which reuses the chip-search-* tokens above).
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

        // Deliberately stronger than --p-content-hover-background (which is
        // tuned for subtle hoverable rows/lists) — ghost/secondary buttons
        // need a more perceptible hover cue.
        "--arches-search-sec-btn-hover-bg": "#e2e8f0",

        // Deliberately stronger than --p-text-muted-color — ghost/secondary
        // button labels need to read as legible text, not a disabled hint.
        "--arches-search-sec-btn-text": "#475569",

        // Deliberately stronger than --p-content-border-color (which is
        // tuned for subtle content-area separators) — filter/toggle chips
        // need a more defined outline than that.
        "--arches-search-chip-border": "#cbd5e1",
    },
    ".p-theme-dark": {
        // True neutral (R=G=B) greyscale, not Tailwind's slate/gray families
        // used elsewhere in this file for accents — slate/gray both carry a
        // cool blue tint that reads as "navy" once it covers this much
        // surface area, which is wrong for a plain dark background.
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
