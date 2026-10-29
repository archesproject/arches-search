import type { ResourceModel } from "@/arches_search/RelationshipGraph/types.ts";

const FALLBACK_PALETTE = [
    "#4e79a7",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc948",
    "#b07aa1",
    "#ff9da7",
    "#9c755f",
    "#bab0ac",
];

// Module-level so the summary swatches and the graph nodes always agree on
// the color of a model that has none configured.
const fallbackColors = new Map<string, string>();

export function useGraphColors() {
    function colorFor(model: Pick<ResourceModel, "id" | "color">): string {
        if (model.color) return model.color;

        let fallback = fallbackColors.get(model.id);
        if (!fallback) {
            fallback =
                FALLBACK_PALETTE[fallbackColors.size % FALLBACK_PALETTE.length];
            fallbackColors.set(model.id, fallback);
        }
        return fallback;
    }

    return { colorFor };
}
