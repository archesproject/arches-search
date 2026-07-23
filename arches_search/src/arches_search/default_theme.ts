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
    },
    ".p-theme-dark": {
        "--arches-search-page-bg": "#0a0e15",
        "--arches-search-card-bg": "#111827",

        "--arches-search-chip-search-bg": "#1e293b",
        "--arches-search-chip-search-border": "#334155",
        "--arches-search-chip-search-text": "#cbd5e1",

        "--arches-search-highlight-bg": "#082f49",
        "--arches-search-highlight-text": "#7dd3fc",

        "--arches-search-live-bg": "#052e16",
        "--arches-search-live-text": "#4ade80",
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
            fontSize: "1.4rem",
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
