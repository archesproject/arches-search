<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import ResourceRelationshipSummary from "@/arches_search/RelationshipGraph/components/ResourceRelationshipSummary.vue";
import { useRelationshipSummaries } from "@/arches_search/RelationshipGraph/composables/useRelationshipSummaries.ts";

import type { SelectedResource } from "@/arches_search/RelationshipGraph/types.ts";

const { resources } = defineProps<{
    resources: SelectedResource[];
}>();

const emit = defineEmits<{
    (event: "remove-resource", resourceId: string): void;
    (event: "close"): void;
}>();

const { $gettext, $ngettext } = useGettext();

const {
    summaryStates,
    deselectedRowIds,
    selectedRelationshipCount,
    isLoading,
    toggleRow,
    loadSummary,
} = useRelationshipSummaries(() => resources.map((resource) => resource.id));

const isGraphVisible = ref(false);

const panelTitle = computed<string>(() =>
    resources.length === 1
        ? $gettext("%{title}: related resources", {
              title: resources[0].title,
          })
        : $gettext("Related resources"),
);

const showRelationshipsLabel = computed<string>(() =>
    selectedRelationshipCount.value > 0
        ? $ngettext(
              "Show %{count} relationship",
              "Show %{count} relationships",
              selectedRelationshipCount.value,
              { count: String(selectedRelationshipCount.value) },
          )
        : $gettext("Show relationships"),
);

const canShowRelationships = computed<boolean>(
    () => !isLoading.value && selectedRelationshipCount.value > 0,
);
</script>

<template>
    <div class="relationship-graph">
        <div class="header">
            <h3 class="title">
                <i class="pi pi-sitemap" />
                <span>{{ panelTitle }}</span>
            </h3>
            <Button
                class="back"
                icon="pi pi-arrow-left"
                variant="link"
                :label="$gettext('Back')"
                @click="emit('close')"
            />
        </div>

        <div
            v-if="isGraphVisible"
            class="graph-placeholder"
        >
            <i class="pi pi-share-alt" />
            <span>{{ $gettext("The graph is not available yet.") }}</span>
        </div>

        <div
            v-else
            class="summaries"
        >
            <ResourceRelationshipSummary
                v-for="resource in resources"
                :key="resource.id"
                :title="resource.title"
                :summary-state="summaryStates[resource.id]"
                :deselected-row-ids="deselectedRowIds[resource.id] ?? []"
                @toggle-row="toggleRow(resource.id, $event)"
                @retry="loadSummary(resource.id)"
                @remove="emit('remove-resource', resource.id)"
            />
        </div>

        <div class="footer">
            <Button
                v-if="isGraphVisible"
                class="footer-btn"
                icon="pi pi-list"
                icon-pos="left"
                severity="secondary"
                :label="$gettext('Back to summary')"
                @click="isGraphVisible = false"
            />
            <Button
                v-else
                class="footer-btn"
                icon="pi pi-share-alt"
                icon-pos="left"
                :label="showRelationshipsLabel"
                :disabled="!canShowRelationships"
                @click="isGraphVisible = true"
            />
        </div>
    </div>
</template>

<style scoped>
.relationship-graph {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--arches-search-card-bg);
}

.relationship-graph .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 2rem 2rem 0.75rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.relationship-graph .header .title {
    margin: 0;
    display: flex;
    align-items: center;
    min-width: 0;
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--p-text-color);
}

.relationship-graph .header .title .pi {
    margin-inline-end: 0.6rem;
    color: var(--p-primary-color);
    flex-shrink: 0;
}

.relationship-graph .header .title span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.relationship-graph .header .back.p-button {
    flex-shrink: 0;
    padding: 0.3rem 0.8rem;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--p-text-muted-color);
    border-radius: 0.4rem;
    text-decoration: none;
}

.relationship-graph .header .back.p-button:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.relationship-graph .summaries {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 2.4rem;
    min-block-size: 0;
    padding: 1.6rem 2rem;
    overflow-y: auto;
}

.relationship-graph .graph-placeholder {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.2rem;
    color: var(--p-text-muted-color);
    font-size: 1.4rem;
}

.relationship-graph .graph-placeholder .pi {
    font-size: 4.8rem;
    opacity: 0.3;
}

.relationship-graph .footer {
    display: flex;
    justify-content: flex-end;
    padding: 1.2rem 2rem;
    border-block-start: 0.125rem solid var(--p-content-border-color);
}

/* At least as large as the resource type chips in the search toolbar (1.2rem) */
.relationship-graph .footer .footer-btn.p-button {
    font-size: 1.4rem;
    font-weight: 600;
}
</style>
