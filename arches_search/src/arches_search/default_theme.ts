import { definePreset } from "@primeuix/themes";
import Aura from "@primeuix/themes/aura";

import { compileGlobalCss } from "@/arches_modular_reports/utils.ts";

const cssOverrides = {
    // examples of how to override styles in modular report components
    // ".section-table-header h4": {
    //     padding: "0 2rem !important",
    //     "font-size": "1.5rem !important",
    // },
    // ".linked-section-container": {
    //     margin: "0 1.5rem !important",
    // },
    // ".linked-section-container .p-panel-header h3": {
    //     "font-size": "2.5rem !important",
    // },
    // ".linked-section-button-container .p-button-label": {
    //     color: "#1857e5",
    // },
    // ".p-card-content h2": {
    //     "font-size": "3rem !important",
    // },
    // ".node-container strong": {
    //     "font-size": "1.7rem !important",
    // },
    // "button.p-tab": {
    //     "font-size": "1.6rem !important",
    // },
    // ".p-tabpanels": {
    //     "background-color": "#e9ebed",
    // },
    // ".data-container": {
    //     border: "0",
    //     margin: "0 4.5rem 3rem !important",
    //     "grid-template-columns": "repeat(4, 1fr) !important",
    // },
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
const ModularReportPreset = definePreset(Aura, {
    extend: {
        archesSearch: {
            fontSize: "1.4rem",
        },
    },
    semantic: {
        primary: {
            50: "{amber.50}",
            100: "{amber.100}",
            200: "{amber.200}",
            300: "{amber.300}",
            400: "{amber.400}",
            500: "{amber.500}",
            600: "{amber.600}",
            700: "{amber.700}",
            800: "{amber.800}",
            900: "{amber.900}",
            950: "{amber.950}",
        },
        colorScheme: {
            light: {
                // primary: {
                //     color: "{sky.700}",
                //     inverseColor: "#ffffff",
                //     hoverColor: "{sky.900}",
                //     activeColor: "{sky.800}",
                // },
                // highlight: {
                //     background: "{sky.300}",
                //     focusBackground: "{sky.700}",
                //     color: "#ffffff",
                //     focusColor: "#ffffff",
                // }
            },
            dark: {
                // primary: {
                //     color: "{sky.300}",
                //     inverseColor: "{sky.950}",
                //     hoverColor: "{sky.100}",
                //     activeColor: "{sky.200}",
                // },
                // highlight: {
                //     background: "rgba(250, 250, 250, .16)",
                //     focusBackground: "rgba(250, 250, 250, .24)",
                //     color: "rgba(255,255,255,.87)",
                //     focusColor: "rgba(255,255,255,.87)",
                // },
            },
        },
    },
    css: compileGlobalCss(cssOverrides),
    components: {},
});

export default {
    theme: {
        ...DEFAULT_THEME.theme,
        preset: ModularReportPreset,
    },
};
