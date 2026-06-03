<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Accordion from "primevue/accordion";
import AccordionPanel from "primevue/accordionpanel";
import AccordionHeader from "primevue/accordionheader";
import AccordionContent from "primevue/accordioncontent";

import { getAttributeFilterEntry } from "@/arches_search/SimpleSearch/components/attribute-filters/registry.ts";

import type { Component } from "vue";
import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();

defineProps<{
    nodes: NodeFilterConfigNode[];
    values: Record<string, unknown>;
}>();

const emit = defineEmits<{
    (event: "update:value", nodeAlias: string, value: unknown): void;
}>();

function componentFor(node: NodeFilterConfigNode): Component | null {
    return getAttributeFilterEntry(node.datatype)?.component ?? null;
}
</script>

<template>
    <div class="attribute-filters">
        <h3 class="filters-heading">{{ $gettext("Attribute Filters") }}</h3>

        <Accordion
            multiple
            :value="[]"
        >
            <AccordionPanel
                v-for="node in nodes"
                :key="node.node_alias"
                :value="node.node_alias"
            >
                <AccordionHeader>{{ node.label }}</AccordionHeader>
                <AccordionContent>
                    <component
                        :is="componentFor(node)"
                        v-if="componentFor(node)"
                        :node="node"
                        :model-value="values[node.node_alias] ?? null"
                        @update:model-value="
                            emit('update:value', node.node_alias, $event)
                        "
                    />
                    <div
                        v-else
                        class="unsupported"
                    >
                        {{
                            $gettext(
                                "Filtering is not supported for this field yet.",
                            )
                        }}
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

.unsupported {
    font-size: var(--p-arches-search-font-size);
    color: var(--p-surface-400);
    padding: 0.4rem 0 0.8rem 0;
}
</style>
