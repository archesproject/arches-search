import type { Component } from "vue";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";

// A single selectable reference value (controlled-list item).
export interface ReferenceFilterOption {
    id: string;
    label: string;
}

// The reference filter carries the selected options (id + label). The label
// is retained so the query builder can send labels as operands without
// re-resolving against the loaded option list.
export type ReferenceFilterValue = ReferenceFilterOption[];

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
}
