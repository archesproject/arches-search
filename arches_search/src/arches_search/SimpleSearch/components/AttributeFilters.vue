<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Accordion from "primevue/accordion";
import AccordionPanel from "primevue/accordionpanel";
import AccordionHeader from "primevue/accordionheader";
import AccordionContent from "primevue/accordioncontent";
import Checkbox from "primevue/checkbox";

import type { AttributeFilterSection } from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();

const props = defineProps<{
    sections: AttributeFilterSection[];
    selectedOptions: Record<string, string[]>;
}>();

const emit = defineEmits<{
    (event: "update:selectedOptions", value: Record<string, string[]>): void;
}>();

function isChecked(sectionId: string, optionId: string): boolean {
    return (props.selectedOptions[sectionId] || []).includes(optionId);
}

function toggleOption(sectionId: string, optionId: string) {
    const updated = { ...props.selectedOptions };
    const current = [...(updated[sectionId] || [])];
    const idx = current.indexOf(optionId);

    if (idx >= 0) {
        current.splice(idx, 1);
    } else {
        current.push(optionId);
    }

    updated[sectionId] = current;
    emit("update:selectedOptions", updated);
}
</script>

<template>
    <div class="attribute-filters">
        <h3 class="filters-heading">{{ $gettext("Attribute Filters") }}</h3>

        <Accordion
            multiple
            :value="sections.map((s) => s.id)"
        >
            <AccordionPanel
                v-for="section in sections"
                :key="section.id"
                :value="section.id"
            >
                <AccordionHeader>{{ section.label }}</AccordionHeader>
                <AccordionContent>
                    <div
                        v-if="section.options.length === 0"
                        class="no-options"
                    >
                        {{ $gettext("No options available") }}
                    </div>
                    <div
                        v-else
                        class="filter-options"
                    >
                        <label
                            v-for="option in section.options"
                            :key="option.id"
                            :for="`${section.id}-${option.id}`"
                            class="filter-option"
                        >
                            <Checkbox
                                :input-id="`${section.id}-${option.id}`"
                                :model-value="isChecked(section.id, option.id)"
                                binary
                                @update:model-value="
                                    toggleOption(section.id, option.id)
                                "
                            />
                            <span class="option-label">{{ option.label }}</span>
                            <span
                                v-if="option.count !== undefined"
                                class="option-count"
                            >
                                ({{ option.count }})
                            </span>
                        </label>
                    </div>
                </AccordionContent>
            </AccordionPanel>
        </Accordion>
    </div>
</template>

<style scoped>
.attribute-filters {
    height: 100%;
    overflow-y: auto;
    padding: 1.2rem 1.6rem;
}

.filters-heading {
    margin: 0 0 1.2rem 0;
}

.filter-options {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    padding: .4rem 0 .8rem 0;
}

.filter-option {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    cursor: pointer;
    font-size: var(--p-arches-search-font-size);
}

.option-label {
    flex: 1;
    color: var(--p-surface-800);
}

.option-count {
    color: var(--p-surface-400);
    font-size: var(--p-arches-search-font-size);
}

.no-options {
    font-size: var(--p-arches-search-font-size);
    color: var(--p-surface-400);
    padding: .4rem 0 .8rem 0;
}
</style>
