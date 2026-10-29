import {
    FADED_CLASS,
    ON_PATH_CLASS,
    SEED_CLASS,
} from "@/arches_search/RelationshipGraph/utils/graph-elements.ts";

import type { StylesheetJson } from "cytoscape";

export interface GraphTheme {
    label: string;
    labelOutline: string;
    nodeBorder: string;
    seedBorder: string;
    edge: string;
    path: string;
}

// A canvas cannot read CSS variables, so the theme is resolved up front and
// these are what it falls back to if a token is missing
const FALLBACK_THEME: GraphTheme = {
    label: "#1e293b",
    labelOutline: "#ffffff",
    nodeBorder: "#ffffff",
    seedBorder: "#1e293b",
    edge: "#94a3b8",
    path: "#0d9488",
};

const LABEL_FONT_SIZE = 11;
const LABEL_MAX_WIDTH = "110px";
const LABEL_OUTLINE_WIDTH = 2;
const LABEL_MIN_ZOOMED_FONT_SIZE = 8;
const NODE_BORDER_WIDTH = 2;
const SEED_BORDER_WIDTH = 4;
const EDGE_WIDTH = 1.5;
const PATH_BORDER_WIDTH = 4;
const PATH_EDGE_WIDTH = 3.5;
const FADED_OPACITY = 0.3;
const ARROW_SCALE = 0.9;

const RESOLVED_COLOR_PATTERN = /^(rgb|rgba|#)/;

// Asks the browser to resolve a token (which may itself be a var()) to a
// concrete color, which is what Cytoscape needs. A token the theme does not
// define would resolve to whatever color is inherited, so those are left to
// the fallback.
function resolveColor(
    container: HTMLElement,
    token: string,
    fallback: string,
): string {
    if (!getComputedStyle(container).getPropertyValue(token).trim()) {
        return fallback;
    }

    const probe = document.createElement("span");
    probe.style.color = `var(${token})`;
    container.appendChild(probe);
    const resolved = getComputedStyle(probe).color;
    container.removeChild(probe);
    return RESOLVED_COLOR_PATTERN.test(resolved) ? resolved : fallback;
}

export function readGraphTheme(container: HTMLElement): GraphTheme {
    return {
        label: resolveColor(container, "--p-text-color", FALLBACK_THEME.label),
        labelOutline: resolveColor(
            container,
            "--arches-search-card-bg",
            FALLBACK_THEME.labelOutline,
        ),
        nodeBorder: resolveColor(
            container,
            "--arches-search-card-bg",
            FALLBACK_THEME.nodeBorder,
        ),
        seedBorder: resolveColor(
            container,
            "--p-text-color",
            FALLBACK_THEME.seedBorder,
        ),
        edge: resolveColor(container, "--p-surface-400", FALLBACK_THEME.edge),
        path: resolveColor(container, "--p-primary-color", FALLBACK_THEME.path),
    };
}

export function buildGraphStylesheet(theme: GraphTheme): StylesheetJson {
    return [
        {
            selector: "node",
            style: {
                "background-color": "data(color)",
                width: "data(size)",
                height: "data(size)",
                label: "data(label)",
                color: theme.label,
                "font-size": LABEL_FONT_SIZE,
                "text-valign": "bottom",
                "text-halign": "center",
                "text-margin-y": 4,
                "text-wrap": "ellipsis",
                "text-max-width": LABEL_MAX_WIDTH,
                "text-outline-color": theme.labelOutline,
                "text-outline-width": LABEL_OUTLINE_WIDTH,
                "min-zoomed-font-size": LABEL_MIN_ZOOMED_FONT_SIZE,
                "border-width": NODE_BORDER_WIDTH,
                "border-color": theme.nodeBorder,
            },
        },
        {
            selector: `node.${SEED_CLASS}`,
            style: {
                "border-width": SEED_BORDER_WIDTH,
                "border-color": theme.seedBorder,
                "font-weight": "bold",
                "z-index": 10,
            },
        },
        {
            selector: `node.${ON_PATH_CLASS}`,
            style: {
                "border-width": PATH_BORDER_WIDTH,
                "border-color": theme.path,
                "z-index": 10,
            },
        },
        {
            selector: "edge",
            style: {
                width: EDGE_WIDTH,
                "line-color": theme.edge,
                "target-arrow-color": theme.edge,
                "target-arrow-shape": "triangle",
                "arrow-scale": ARROW_SCALE,
                "curve-style": "bezier",
            },
        },
        {
            selector: `edge.${ON_PATH_CLASS}`,
            style: {
                width: PATH_EDGE_WIDTH,
                "line-color": theme.path,
                "target-arrow-color": theme.path,
                "z-index": 9,
            },
        },
        {
            selector: `.${FADED_CLASS}`,
            style: {
                opacity: FADED_OPACITY,
            },
        },
    ];
}
