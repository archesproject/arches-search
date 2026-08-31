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

        "--arches-search-card-border": "#e2e8f0",
        "--arches-search-card-shadow":
            "0 0.1rem 0.3rem rgba(0, 0, 0, 0.06), 0 0.1rem 0.2rem rgba(0, 0, 0, 0.04)",
        "--arches-search-card-shadow-hover": "0 0.6rem 2rem rgba(0, 0, 0, 0.1)",
        "--arches-search-item-hover-shadow":
            "0 0.1rem 0.3rem rgba(0, 0, 0, 0.08)",
        "--arches-search-overlay-shadow":
            "0 0.8rem 2.4rem rgba(0, 0, 0, 0.12), 0 0.2rem 0.6rem rgba(0, 0, 0, 0.07)",
        "--arches-search-primary-muted-bg": "rgba(13, 148, 136, 0.1)",

        "--arches-search-model-card-radius": "0.4rem",
        "--arches-search-model-icon-radius": "0.9rem",
        "--arches-search-model-icon-text": "#ffffff",
        "--arches-search-model-icon-color-1": "#f97316",
        "--arches-search-model-icon-color-2": "#06b6d4",
        "--arches-search-model-icon-color-3": "#8b5cf6",
        "--arches-search-model-icon-color-4": "#ec4899",
        "--arches-search-model-icon-color-5": "#f59e0b",
        "--arches-search-model-icon-color-6": "#0d9488",
        "--arches-search-model-icon-color-7": "#6366f1",
        "--arches-search-model-icon-color-8": "#84cc16",

        "--arches-search-hero-gradient":
            "linear-gradient(145deg, #0c1520 0%, #162032 45%, #1a2e3a 75%, #0e2a27 100%)",
        "--arches-search-hero-dot-grid":
            "radial-gradient(rgba(255, 255, 255, 0.055) 0.1rem, transparent 0.1rem)",
        "--arches-search-hero-dot-grid-size": "3.2rem 3.2rem",
        "--arches-search-hero-glow":
            "radial-gradient(circle, rgba(13, 148, 136, 0.22) 0%, transparent 65%)",
        "--arches-search-hero-glow-size": "48rem",
        "--arches-search-hero-glow-offset": "-8rem",
        "--arches-search-hero-eyebrow-bg": "rgba(13, 148, 136, 0.18)",
        "--arches-search-hero-eyebrow-border": "rgba(13, 148, 136, 0.35)",
        "--arches-search-hero-eyebrow-text": "#5eead4",
        "--arches-search-hero-title-text": "#ffffff",
        "--arches-search-hero-subtitle-text": "rgba(255, 255, 255, 0.56)",
        "--arches-search-hero-search-bg": "rgba(255, 255, 255, 0.97)",
        "--arches-search-hero-search-radius": "3.6rem",
        "--arches-search-hero-search-shadow":
            "0 1.2rem 4rem rgba(0, 0, 0, 0.3), 0 0 0 0.1rem rgba(255, 255, 255, 0.2)",
        "--arches-search-hero-search-btn-font-size": "1.4rem",
        "--arches-search-hero-search-btn-font-weight": "600",
        "--arches-search-hero-hint-text": "rgba(255, 255, 255, 0.44)",
        "--arches-search-hero-hint-text-hover": "rgba(255, 255, 255, 0.78)",
        "--arches-search-hero-link-text": "rgba(255, 255, 255, 0.54)",
        "--arches-search-hero-link-text-hover": "rgba(255, 255, 255, 0.9)",
        "--arches-search-hero-toggle-border": "rgba(255, 255, 255, 0.14)",
        "--arches-search-hero-toggle-bg": "rgba(255, 255, 255, 0.08)",
        "--arches-search-hero-toggle-bg-hover": "rgba(255, 255, 255, 0.16)",
        "--arches-search-hero-toggle-text": "rgba(255, 255, 255, 0.7)",
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

        "--arches-search-card-border": "#1e293b",
        "--arches-search-card-shadow":
            "0 0.1rem 0.3rem rgba(0, 0, 0, 0.3), 0 0.1rem 0.2rem rgba(0, 0, 0, 0.2)",
        "--arches-search-card-shadow-hover": "0 0.6rem 2rem rgba(0, 0, 0, 0.5)",
        "--arches-search-item-hover-shadow":
            "0 0.1rem 0.3rem rgba(0, 0, 0, 0.4)",
        "--arches-search-overlay-shadow":
            "0 0.8rem 2.4rem rgba(0, 0, 0, 0.6), 0 0.2rem 0.6rem rgba(0, 0, 0, 0.35)",
        "--arches-search-primary-muted-bg": "rgba(13, 148, 136, 0.14)",

        "--arches-search-hero-search-bg": "rgba(17, 24, 39, 0.97)",
        "--arches-search-hero-search-shadow":
            "0 1.2rem 4rem rgba(0, 0, 0, 0.5), 0 0 0 0.1rem rgba(255, 255, 255, 0.08)",
    },
};

// Matches createVueApplication()'s darkModeSelector-derived localStorage key
// convention (arches_vue_components/application/create-vue-application.ts),
// so a toggle here stays in sync with the class applied at app boot.
export const DARK_MODE_CLASS = "p-theme-dark";
export const DARK_MODE_STORAGE_KEY = `arches.${DARK_MODE_CLASS}`;

// TODO: when dropping support for 7.6, just import from arches 8.
const DEFAULT_THEME = {
    theme: {
        // preset: ArchesPreset,
        options: {
            prefix: "p",
            darkModeSelector: `.${DARK_MODE_CLASS}`,
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
