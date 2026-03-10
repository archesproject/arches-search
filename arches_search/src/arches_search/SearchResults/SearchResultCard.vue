<script setup lang="ts">
import { computed, provide, ref, toRef, watchEffect } from "vue";

import { importComponents } from "@/arches_modular_reports/ModularReport/utils.ts";
import ExpandedResultSection from "@/arches_search/SearchResults/components/ExpandedResultSection.vue";

import type { ComponentLookup } from "@/arches_modular_reports/ModularReport/types.ts";
import type { ResourceData } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    ResourceDescriptorData,
    SearchReportConfig,
} from "@/arches_search/SearchResults/types.ts";

const props = defineProps<{
    result: ResourceData;
    descriptorData: ResourceDescriptorData | null;
    reportConfig: SearchReportConfig | null;
}>();

const componentLookup: ComponentLookup = {};

const isExpanded = ref(false);

// Provide context for injected child components (DescriptorSection, ExpandedResultSection, etc.)
provide("resourceInstanceId", props.result.resourceinstanceid);
provide("descriptorData", toRef(props, "descriptorData"));
provide("searchResultExpanded", isExpanded);

// Read-only stubs for DataSection edit-path injections.
// DataSection destructures these without null guards, so they must be provided.
provide("userCanEditResourceInstance", ref(false));
provide("createTile", {
    createTileRequestId: ref(0),
    createTileRequestedNodegroupAlias: ref(null),
    createTileRequestedTilePath: ref(null),
    requestCreateTile: () => {},
});
provide("softDeleteTile", {
    softDeleteTileRequestId: ref(0),
    softDeleteRequestedNodegroupAlias: ref(null),
    softDeleteRequestedTileId: ref(null),
    requestSoftDeleteTile: () => {},
});
provide("selectedNodegroupAlias", {
    selectedNodegroupAlias: ref(null),
    setSelectedNodegroupAlias: () => {},
});
provide("selectedNodeAlias", {
    selectedNodeAlias: ref(null),
    setSelectedNodeAlias: () => {},
});
provide("selectedTileId", {
    selectedTileId: ref(null),
    setSelectedTileId: () => {},
});
provide("selectedTilePath", {
    selectedTilePath: ref(null),
    setSelectedTilePath: () => {},
});
provide("shouldShowEditor", {
    shouldShowEditor: ref(false),
    setShouldShowEditor: () => {},
});

const configAsNamedSection = computed(() => ({
    name: props.reportConfig?.name ?? "",
    components: props.reportConfig?.components ?? [],
}));

watchEffect(() => {
    if (props.reportConfig?.components?.length) {
        importComponents([configAsNamedSection.value], componentLookup);
    }
});
</script>

<template>
    <div class="search-result-card">
        <component
            :is="componentLookup[component.component]?.component"
            v-for="component in configAsNamedSection.components"
            :key="componentLookup[component.component]?.key"
            :component
            :resource-instance-id="result.resourceinstanceid"
        />
        <ExpandedResultSection />
    </div>
</template>

<style scoped>
.search-result-card {
    border-bottom: 0.125rem solid var(--p-content-border-color);
}
</style>
