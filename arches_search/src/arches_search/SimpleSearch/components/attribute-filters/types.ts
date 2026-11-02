import type { Component } from "vue";

import type { ReferenceSelectNodeValue } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";

// The list items chosen, as the reference widget saves them; a search saved
// before that holds only their labels.
export type ReferenceFilterValue = ReferenceSelectNodeValue[] | string[];

// One parsed segment of a numeric expression like "9-10, 12".
export type NumericToken =
    | { kind: "value"; value: number }
    | { kind: "range"; min: number; max: number };

export interface NumericFilterValue {
    // The raw text the user typed, retained so the input can round-trip.
    text: string;
    tokens: NumericToken[];
}

// A datatype's filter: the widget rendered inside its accordion panel and the
// pure function that turns the widget's emitted value into a search query.
// `value` is the datatype-specific value emitted by `component`; each builder
// narrows it to its own value type. Returning `null` clears the node's query.
export interface AttributeFilterEntry {
    component: Component;
    buildQuery(
        node: NodeFilterConfigNode,
        value: unknown,
        graphSlug: string,
    ): GroupPayload | null;
    // Renders the widget's current value as chip-friendly display text (for
    // the active-filters row) — kept per-datatype here alongside buildQuery
    // since both are just different views of the same datatype-specific value.
    formatValue(value: unknown): string;
    // The inverse of buildQuery, for a query restored from a saved search
    // rather than built from this widget.
    parseValue(query: GroupPayload): unknown;
}
