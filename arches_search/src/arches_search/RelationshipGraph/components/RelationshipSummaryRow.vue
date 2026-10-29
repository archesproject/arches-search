<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { useGraphColors } from "@/arches_search/RelationshipGraph/composables/useGraphColors.ts";

import type { RelationshipSummaryRow } from "@/arches_search/RelationshipGraph/types.ts";

const { row, selected } = defineProps<{
    row: RelationshipSummaryRow;
    selected: boolean;
}>();

const emit = defineEmits<{
    (event: "toggle"): void;
}>();

const { $gettext } = useGettext();
const { colorFor } = useGraphColors();

const swatchColor = computed<string>(() => colorFor(row.related_model));

const typeLabel = computed<string>(
    () => row.relationship_type_label || $gettext("Unspecified relationship"),
);

const isOutgoing = computed<boolean>(() => row.direction === "outgoing");

const directionLabel = computed<string>(() =>
    isOutgoing.value ? $gettext("Outgoing") : $gettext("Incoming"),
);

const toggleLabel = computed<string>(() =>
    selected
        ? $gettext("Hide %{type} relationships to %{model} from the graph", {
              type: typeLabel.value,
              model: row.related_model.name,
          })
        : $gettext("Show %{type} relationships to %{model} in the graph", {
              type: typeLabel.value,
              model: row.related_model.name,
          }),
);
</script>

<template>
    <li
        class="relationship-summary-row"
        :class="{ 'relationship-summary-row-off': !selected }"
    >
        <span
            class="swatch"
            :style="{ backgroundColor: swatchColor }"
        />
        <div class="details">
            <span class="model-name">{{ row.related_model.name }}</span>
            <span class="relationship-type">
                <i
                    role="img"
                    :class="[
                        'pi',
                        isOutgoing ? 'pi-arrow-right' : 'pi-arrow-left',
                    ]"
                    :title="directionLabel"
                    :aria-label="directionLabel"
                />
                <span>{{ typeLabel }}</span>
            </span>
        </div>
        <span class="count">{{ row.count }}</span>
        <Button
            class="toggle"
            variant="text"
            size="small"
            :icon="selected ? 'pi pi-eye' : 'pi pi-eye-slash'"
            :aria-label="toggleLabel"
            :aria-pressed="selected"
            :title="toggleLabel"
            @click="emit('toggle')"
        />
    </li>
</template>

<style scoped>
.relationship-summary-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.8rem 0;
    border-block-end: 0.0625rem solid var(--p-content-border-color);
    transition: opacity 0.15s ease;
}

.relationship-summary-row.relationship-summary-row-off {
    opacity: 0.5;
}

.relationship-summary-row .swatch {
    flex-shrink: 0;
    inline-size: 1.4rem;
    block-size: 1.4rem;
    border-radius: 50%;
    border: 0.125rem solid var(--p-content-background);
    box-shadow: 0 0 0 0.0625rem var(--p-content-border-color);
}

.relationship-summary-row .details {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 0.2rem;
    min-inline-size: 0;
}

.relationship-summary-row .details .model-name {
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--p-text-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.relationship-summary-row .details .relationship-type {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.3rem;
    color: var(--p-text-muted-color);
    min-inline-size: 0;
}

.relationship-summary-row .details .relationship-type .pi {
    flex-shrink: 0;
    font-size: 1.1rem;
}

.relationship-summary-row .details .relationship-type span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.relationship-summary-row .count {
    flex-shrink: 0;
    min-inline-size: 2.6rem;
    padding: 0.2rem 0.8rem;
    border-radius: var(--arches-search-radius-pill);
    background: var(--arches-search-chip-search-bg);
    color: var(--arches-search-chip-search-text);
    font-size: 1.2rem;
    font-weight: 600;
    text-align: center;
}

.relationship-summary-row .toggle {
    flex-shrink: 0;
}
</style>
