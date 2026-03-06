<script setup lang="ts">
import { ref } from "vue";
import { useGettext } from "vue3-gettext";

import Dialog from "primevue/dialog";
import Tabs from "primevue/tabs";
import TabList from "primevue/tablist";
import Tab from "primevue/tab";
import TabPanels from "primevue/tabpanels";
import TabPanel from "primevue/tabpanel";

import PayloadAnalyzerNarrationPanel from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/components/NarrationPanel/NarrationPanel.vue";
import PayloadAnalyzerPayloadPanel from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/components/PayloadPanel.vue";
import PayloadAnalyzerSQLPanel from "@/arches_search/AdvancedSearch/components/PayloadAnalyzer/components/SQLPanel.vue";

import type {
    AdvancedSearchFacet,
    GraphModel,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const SQL = "sql";
const NARRATION = "narration";
const PAYLOAD = "payload";

defineProps<{
    visible: boolean;
    payload: GroupPayload;
    graphs: GraphModel[];
    datatypesToAdvancedSearchFacets: Record<string, AdvancedSearchFacet[]>;
}>();

const emit = defineEmits<{
    "update:visible": [value: boolean];
}>();

const activeTabValue = ref(SQL);

function onUpdateVisible(nextVisible: boolean) {
    emit("update:visible", nextVisible);
}
</script>

<template>
    <Dialog
        :visible="visible"
        :modal="true"
        :draggable="false"
        :resizable="true"
        :dismissable-mask="true"
        :style="{ maxWidth: '100vw' }"
        :header="$gettext('Describe Query')"
        @update:visible="onUpdateVisible"
    >
        <div class="payload-analyzer">
            <Tabs
                v-model:value="activeTabValue"
                class="payload-analyzer-tabs"
            >
                <TabList>
                    <Tab :value="SQL">
                        {{ $gettext("SQL") }}
                    </Tab>
                    <Tab :value="NARRATION">
                        {{ $gettext("Natural Language") }}
                    </Tab>
                    <Tab :value="PAYLOAD">
                        {{ $gettext("Payload") }}
                    </Tab>
                </TabList>

                <TabPanels class="payload-analyzer-tabpanels">
                    <TabPanel :value="SQL">
                        <PayloadAnalyzerSQLPanel :payload="payload" />
                    </TabPanel>

                    <TabPanel :value="NARRATION">
                        <PayloadAnalyzerNarrationPanel
                            :payload="payload"
                            :graphs="graphs"
                            :datatypes-to-advanced-search-facets="
                                datatypesToAdvancedSearchFacets
                            "
                        />
                    </TabPanel>

                    <TabPanel :value="PAYLOAD">
                        <PayloadAnalyzerPayloadPanel :payload="payload" />
                    </TabPanel>
                </TabPanels>
            </Tabs>
        </div>
    </Dialog>
</template>

<style scoped>
.payload-analyzer-tabpanels {
    margin-top: 1rem;
}

:deep(.payload-analyzer-textarea) {
    min-width: 80vw;
    width: 100%;
    font-family: var(--p-font-family);
    font-size: 1.2rem;
}

:deep(.payload-analyzer-textarea textarea) {
    resize: both;
}
</style>
