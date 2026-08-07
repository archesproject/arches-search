<script setup lang="ts">
import { inject, provide, ref, watch } from "vue";

import { fetchNodePresentation } from "@/arches_modular_reports/ModularReport/api.ts";
import { importComponents } from "@/arches_modular_reports/ModularReport/utils.ts";
import { fetchSearchReportConfig } from "@/arches_search/SearchResults/api.ts";

import type { Ref } from "vue";
import type {
    ComponentLookup,
    NodePresentationLookup,
} from "@/arches_modular_reports/ModularReport/types.ts";
import type { SearchReportConfig } from "@/arches_search/SearchResults/types.ts";

const resourceInstanceId = inject("resourceInstanceId") as string;
const isExpanded = inject("searchResultExpanded") as Ref<boolean>;

const nodePresentationLookup = ref<NodePresentationLookup | undefined>();
provide("nodePresentationLookup", nodePresentationLookup);

const expandedConfig = ref<SearchReportConfig | null>(null);
const expandedComponentLookup: ComponentLookup = {};
const isFetchingExpanded = ref(false);

watch(isExpanded, async (expanded) => {
    if (!expanded || expandedConfig.value || isFetchingExpanded.value) return;
    isFetchingExpanded.value = true;
    try {
        const [fetched, nodePresentation] = await Promise.all([
            fetchSearchReportConfig(
                resourceInstanceId,
                "search_result_expanded",
            ),
            fetchNodePresentation(resourceInstanceId),
        ]);
        nodePresentationLookup.value = nodePresentation;
        if (fetched?.components?.length) {
            await importComponents(
                [{ name: "", components: fetched.components }],
                expandedComponentLookup,
            );
        }
        expandedConfig.value = fetched;
    } finally {
        isFetchingExpanded.value = false;
    }
});
</script>

<template>
    <div
        v-if="isExpanded"
        class="expanded-result-section"
    >
        <component
            :is="expandedComponentLookup[comp.component]?.component"
            v-for="comp in expandedConfig?.components ?? []"
            :key="expandedComponentLookup[comp.component]?.key"
            :component="comp"
            :resource-instance-id="resourceInstanceId"
        />
    </div>
</template>

<style scoped>
.expanded-result-section {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
    gap: 0.6rem 1.6rem;
    border-top: 0.1rem dashed var(--p-content-border-color);
    padding: 1rem 1.6rem;
    background-color: var(--arches-search-page-bg);
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
}
</style>
