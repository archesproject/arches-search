<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import RelatedResourceList from "@/arches_search/RelationshipGraph/components/RelatedResourceList.vue";
import { useGraphColors } from "@/arches_search/RelationshipGraph/composables/useGraphColors.ts";

import type { RelationshipSummaryRow } from "@/arches_search/RelationshipGraph/types.ts";

const { resourceId, row, selected } = defineProps<{
    resourceId: string;
    row: RelationshipSummaryRow;
    selected: boolean;
}>();

const emit = defineEmits<{
    (event: "toggle"): void;
}>();

const { $gettext } = useGettext();
const { colorFor } = useGraphColors();

const isExpanded = ref(false);

const swatchColor = computed<string>(() => colorFor(row.related_model));

const typeLabel = computed<string>(
    () => row.relationship_type_label || $gettext("Unspecified relationship"),
);

const listId = computed<string>(
    () => `related-resources-${resourceId}-${row.id}`,
);

const expandLabel = computed<string>(() => {
    if (isExpanded.value) {
        return $gettext(
            "Hide the related %{model} resources",
            { model: row.related_model.name },
            true,
        );
    }
    return $gettext(
        "Show the related %{model} resources",
        { model: row.related_model.name },
        true,
    );
});

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
    <li class="relationship-summary-row">
        <div
            class="summary"
            :class="{ 'summary-off': !selected }"
        >
            <Button
                class="expand"
                variant="text"
                :aria-expanded="isExpanded"
                :aria-controls="isExpanded ? listId : undefined"
                :title="expandLabel"
                @click="isExpanded = !isExpanded"
            >
                <i
                    aria-hidden="true"
                    :class="[
                        'pi',
                        'chevron',
                        isExpanded ? 'pi-chevron-down' : 'pi-chevron-right',
                    ]"
                />
                <span
                    class="swatch"
                    :style="{ backgroundColor: swatchColor }"
                />
                <span class="details">
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
                </span>
                <span class="count">{{ row.count }}</span>
            </Button>
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
        </div>
        <RelatedResourceList
            v-if="isExpanded"
            :id="listId"
            :resource-id="resourceId"
            :row-id="row.id"
        />
    </li>
</template>

<style scoped>
.relationship-summary-row {
    border-block-end: 0.0625rem solid var(--p-content-border-color);
}

.relationship-summary-row .summary {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding-block: 0.8rem;
    transition: opacity 0.15s ease;
}

.relationship-summary-row .summary.summary-off {
    opacity: 0.5;
}

.relationship-summary-row .expand.p-button {
    display: flex;
    flex: 1;
    justify-content: flex-start;
    gap: 1rem;
    min-inline-size: 0;
    padding: 0;
    text-align: start;
}

.relationship-summary-row .expand:hover .model-name {
    text-decoration: underline;
}

.relationship-summary-row .expand .chevron {
    flex-shrink: 0;
    font-size: 1rem;
    color: var(--p-text-muted-color);
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

/* One and a half times a small icon button */
.relationship-summary-row .toggle.p-button {
    flex-shrink: 0;
    inline-size: 3rem;
    block-size: 3rem;
}

/* The icon takes its size from the theme, not from the button */
.relationship-summary-row .toggle.p-button :deep(.p-button-icon) {
    font-size: 1.5rem;
}
</style>
