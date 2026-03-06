<script setup lang="ts">
import { computed, provide, toRef, watchEffect } from "vue";

import { importComponents } from "@/arches_modular_reports/ModularReport/utils.ts";

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

// Provide context for injected child components (DescriptorSection, future DataSection, etc.)
provide("resourceInstanceId", props.result.resourceinstanceid);
provide("descriptorData", toRef(props, "descriptorData"));

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
    </div>
</template>

<style scoped>
.search-result-card {
    border-bottom: 0.125rem solid var(--p-content-border-color);
}
</style>
