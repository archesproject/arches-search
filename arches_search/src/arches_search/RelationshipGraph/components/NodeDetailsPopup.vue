<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Skeleton from "openvue/skeleton";

import { generateArchesURL } from "@/arches_vue_components/application";

import { useResourceDescription } from "@/arches_search/RelationshipGraph/composables/useResourceDescription.ts";

const { resourceId, name, modelName, modelColor, relatedCount } = defineProps<{
    resourceId: string;
    name: string;
    modelName: string;
    modelColor: string;
    relatedCount: number;
}>();

const { $gettext, $ngettext } = useGettext();

const { description, isLoading } = useResourceDescription(() => resourceId);

const relatedCountLabel = computed<string>(() =>
    $ngettext("%{count} relationship", "%{count} relationships", relatedCount, {
        count: String(relatedCount),
    }),
);

const reportLink = computed<string>(() =>
    generateArchesURL("arches:resource_report", { resourceid: resourceId }),
);

const editorLink = computed<string>(() =>
    generateArchesURL("arches:resource_editor", { resourceid: resourceId }),
);
</script>

<template>
    <div class="node-details-popup">
        <header class="header">
            <span
                class="swatch"
                :style="{ backgroundColor: modelColor }"
            />
            <div class="heading">
                <h4 class="name">{{ name }}</h4>
                <span class="model-name">{{ modelName }}</span>
            </div>
        </header>

        <Skeleton
            v-if="isLoading"
            class="description-loading"
        />
        <p
            v-else-if="description"
            class="description"
        >
            {{ description }}
        </p>

        <p class="related-count">{{ relatedCountLabel }}</p>

        <footer class="actions">
            <Button
                as="a"
                icon="pi pi-external-link"
                target="_blank"
                variant="link"
                :href="reportLink"
                :label="$gettext('View Report')"
            />
            <Button
                as="a"
                icon="pi pi-wrench"
                target="_blank"
                variant="link"
                :href="editorLink"
                :label="$gettext('Edit')"
            />
        </footer>
    </div>
</template>

<style scoped>
.node-details-popup {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.node-details-popup .header {
    display: flex;
    align-items: center;
    gap: 1rem;
    /* Clear of the close button */
    padding-inline-end: 3rem;
}

.node-details-popup .header .swatch {
    flex-shrink: 0;
    inline-size: 1.6rem;
    block-size: 1.6rem;
    border-radius: 50%;
}

.node-details-popup .header .heading {
    display: flex;
    flex-direction: column;
    min-inline-size: 0;
}

.node-details-popup .header .heading .name {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--p-text-color);
    overflow-wrap: anywhere;
}

.node-details-popup .header .heading .model-name {
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
}

.node-details-popup .description {
    margin: 0;
    font-size: 1.3rem;
    color: var(--p-text-color);
    overflow-wrap: anywhere;
}

.node-details-popup .description-loading {
    block-size: 3.6rem;
}

.node-details-popup .related-count {
    margin: 0;
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
}

.node-details-popup .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
}
</style>
