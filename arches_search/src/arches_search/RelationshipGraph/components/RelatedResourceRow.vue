<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { generateArchesURL } from "@/arches_vue_components/application";

import type { SelectedResource } from "@/arches_search/RelationshipGraph/types.ts";

const { resourceId, name } = defineProps<{
    resourceId: string;
    name: string;
}>();

const viewRelatedResource = inject<
    ((resource: SelectedResource) => void) | null
>("viewRelatedResource", null);

const { $gettext } = useGettext();

const reportLink = computed<string>(() =>
    generateArchesURL("arches:resource_report", { resourceid: resourceId }),
);

const reportLinkLabel = computed<string>(() =>
    $gettext("View the report of %{name}", { name }, true),
);

const addToPanelLabel = computed<string>(() =>
    $gettext("Show the relationships of %{name} in the panel", { name }, true),
);

function addToPanel(): void {
    viewRelatedResource?.({ id: resourceId, title: name });
}
</script>

<template>
    <li class="related-resource-row">
        <Button
            v-if="viewRelatedResource"
            class="name"
            variant="link"
            :label="name"
            :aria-label="addToPanelLabel"
            :title="addToPanelLabel"
            @click="addToPanel"
        />
        <span
            v-else
            class="name"
            :title="name"
        >
            {{ name }}
        </span>
        <Button
            as="a"
            class="report"
            icon="pi pi-external-link"
            rel="noopener noreferrer"
            target="_blank"
            variant="link"
            :href="reportLink"
            :aria-label="reportLinkLabel"
            :title="reportLinkLabel"
        />
    </li>
</template>

<style scoped>
.related-resource-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    min-inline-size: 0;
    padding-block: 0.2rem;
    font-size: 1.3rem;
    border-block-end: 0.0625rem solid var(--p-content-border-color);
}

.related-resource-row:last-child {
    border-block-end: none;
}

.related-resource-row .name {
    flex: 1;
    min-inline-size: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.related-resource-row span.name {
    color: var(--p-text-color);
}

.related-resource-row .name.p-button {
    justify-content: flex-start;
    padding: 0;
    font-size: inherit;
}

.related-resource-row .name.p-button :deep(.p-button-label) {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* A little larger than a small button, so it reads next to the name */
.related-resource-row .report.p-button {
    flex-shrink: 0;
    inline-size: 2.6rem;
    block-size: 2.6rem;
}

/* The icon takes its size from the theme, not from the button */
.related-resource-row .report.p-button :deep(.p-button-icon) {
    font-size: 1.2rem;
}
</style>
