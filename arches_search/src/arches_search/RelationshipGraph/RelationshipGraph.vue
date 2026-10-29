<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import CytoscapeCanvas from "@/arches_search/RelationshipGraph/components/CytoscapeCanvas.vue";
import GraphControls from "@/arches_search/RelationshipGraph/components/GraphControls.vue";
import ResourcePairSummary from "@/arches_search/RelationshipGraph/components/ResourcePairSummary.vue";
import ResourceRelationshipSummary from "@/arches_search/RelationshipGraph/components/ResourceRelationshipSummary.vue";
import { useFullscreen } from "@/arches_search/RelationshipGraph/composables/useFullscreen.ts";
import { useRelationshipGraph } from "@/arches_search/RelationshipGraph/composables/useRelationshipGraph.ts";
import { useRelationshipSummaries } from "@/arches_search/RelationshipGraph/composables/useRelationshipSummaries.ts";
import { useResourcePath } from "@/arches_search/RelationshipGraph/composables/useResourcePath.ts";

import type { SelectedResource } from "@/arches_search/RelationshipGraph/types.ts";

const { resources } = defineProps<{
    resources: SelectedResource[];
}>();

const emit = defineEmits<{
    (event: "remove-resource", resourceId: string): void;
    (event: "graph-visibility-change", isVisible: boolean): void;
    (event: "close"): void;
}>();

const { $gettext, $ngettext } = useGettext();

const {
    summaryStates,
    deselectedRowIds,
    selectedRelationshipCount,
    selections,
    isLoading,
    toggleRow,
    loadSummary,
} = useRelationshipSummaries(() => resources.map((resource) => resource.id));

const {
    pathState,
    isPathShown,
    shownPathRelationshipIds,
    togglePath,
    loadPath,
} = useResourcePath(() => resources.map((resource) => resource.id));

const isGraphVisible = ref(false);
const stageElement = ref<HTMLDivElement | null>(null);
const canvasRef = ref<InstanceType<typeof CytoscapeCanvas> | null>(null);

const {
    isFullscreen,
    isSupported: isFullscreenSupported,
    toggle: toggleFullscreen,
} = useFullscreen(stageElement);

const {
    graphData,
    isLoading: isGraphLoading,
    hasFailed: hasGraphFailed,
    loadGraph,
} = useRelationshipGraph(selections, isGraphVisible, shownPathRelationshipIds);

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

const graphResourceCountLabel = computed<string>(() => {
    const count = graphData.value?.nodes.length ?? 0;
    return $ngettext(
        "%{count} resource in the graph",
        "%{count} resources in the graph",
        count,
        { count: String(count) },
    );
});

// The graph wants room of its own, which the panel around this makes
watch(isGraphVisible, (isVisible) =>
    emit("graph-visibility-change", isVisible),
);

// Going to or from full screen changes the room the graph has, so it is fitted
// to it. That is two frames on, when the browser has resized the stage.
watch(isFullscreen, () => {
    void nextTick(() => {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => canvasRef.value?.fitToGraph());
        });
    });
});

const truncatedNotice = computed<string>(() =>
    $gettext(
        "Showing the first %{count} resources. Hide some relationships to see the rest.",
        { count: String(graphData.value?.node_limit ?? 0) },
    ),
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
            class="body"
            :class="{ 'body-graph': isGraphVisible }"
        >
            <div
                v-if="isGraphVisible"
                ref="stageElement"
                class="graph-stage"
            >
                <CytoscapeCanvas
                    v-if="graphData"
                    ref="canvasRef"
                    :nodes="graphData.nodes"
                    :edges="graphData.edges"
                />
                <div
                    v-if="isGraphLoading"
                    class="graph-overlay"
                >
                    <i class="pi pi-spin pi-spinner" />
                    <span>{{ $gettext("Loading the graph…") }}</span>
                </div>
                <div
                    v-else-if="hasGraphFailed"
                    class="graph-overlay"
                >
                    <span>{{
                        $gettext("The graph could not be loaded.")
                    }}</span>
                    <Button
                        variant="link"
                        :label="$gettext('Try again')"
                        @click="loadGraph()"
                    />
                </div>
                <p
                    v-if="graphData?.truncated"
                    class="graph-notice"
                >
                    {{ truncatedNotice }}
                </p>
                <GraphControls
                    :is-fullscreen="isFullscreen"
                    :is-fullscreen-supported="isFullscreenSupported"
                    :can-fit="graphData !== null"
                    @close="isGraphVisible = false"
                    @toggle-fullscreen="toggleFullscreen"
                    @fit="canvasRef?.fitToGraph()"
                />
            </div>

            <div class="summaries">
                <p
                    v-if="isGraphVisible && graphData"
                    class="graph-resource-count"
                >
                    <i class="pi pi-share-alt" />
                    <span>{{ graphResourceCountLabel }}</span>
                </p>
                <ResourcePairSummary
                    v-if="resources.length === 2"
                    :from-title="resources[0].title"
                    :to-title="resources[1].title"
                    :path-state="pathState"
                    :is-path-shown="isPathShown"
                    @toggle-path="togglePath"
                    @retry="loadPath()"
                />
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
        </div>

        <div
            v-if="!isGraphVisible"
            class="footer"
        >
            <Button
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

.relationship-graph .body {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-block-size: 0;
}

/* With the graph on show, it takes the left and the summary the right */
.relationship-graph .body.body-graph {
    flex-direction: row;
}

.relationship-graph .body .summaries {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 2.4rem;
    min-block-size: 0;
    padding: 1.6rem 2rem;
    overflow-y: auto;
}

.relationship-graph .body.body-graph .summaries {
    flex: 0 0 38%;
    min-inline-size: 28rem;
    border-inline-start: 0.125rem solid var(--p-content-border-color);
}

.relationship-graph .body .summaries .graph-resource-count {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 0;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--p-text-color);
}

.relationship-graph .body .summaries .graph-resource-count .pi {
    color: var(--p-primary-color);
}

.relationship-graph .body .graph-stage {
    position: relative;
    flex: 1 1 0;
    min-inline-size: 0;
    /* Without one, the full screen shows what is behind it */
    background-color: var(--arches-search-page-bg);
}

.relationship-graph .body .graph-stage .graph-overlay {
    position: absolute;
    inset: 0;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    background: color-mix(
        in srgb,
        var(--arches-search-card-bg) 70%,
        transparent
    );
    color: var(--p-text-muted-color);
    font-size: 1.4rem;
}

.relationship-graph .body .graph-stage .graph-notice {
    position: absolute;
    inset-block-end: 0.8rem;
    inset-inline: 0.8rem;
    z-index: 1;
    margin: 0;
    padding: 0.6rem 1rem;
    border-radius: 0.4rem;
    background: var(--arches-search-highlight-bg);
    color: var(--arches-search-highlight-text);
    font-size: 1.2rem;
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
