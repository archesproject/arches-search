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
        <h3 class="attribute-filters-title">
            {{ $gettext("Attribute Filters") }}
        </h3>

        <span
            v-if="nodes.length === 0"
            class="attribute-filters-empty-state"
        >
            {{
                $gettext(
                    "No filters have been configured for this resource type.",
                )
            }}
        </span>

        <Accordion
            v-else
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
    padding: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
}

.attribute-filters-title {
    margin: 0;
    padding-bottom: 0.75rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--p-text-color);
}

.attribute-filters-empty-state {
    display: block;
    padding: 1rem;
    border: 0.125rem solid var(--p-content-border-color);
    border-radius: 0.5rem;
    font-size: 1rem;
    color: var(--p-text-muted-color);
    line-height: 1.5;
}

.unsupported {
    font-size: 1.3rem;
    color: var(--p-text-muted-color);
    padding: 0.4rem 0 0.8rem 0;
    line-height: 1.5;
}
</style>
