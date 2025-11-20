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
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

type GraphSummary = {
    graphid?: string;
    slug?: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

const { $gettext } = useGettext();

const PAYLOAD = "payload";
const SQL = "sql";
const NARRATION = "narration";

defineProps<{
    visible: boolean;
    payload: GroupPayload;
    graphs: GraphSummary[];
    datatypesToAdvancedSearchFacets: Record<string, AdvancedSearchFacet[]>;
}>();

const emit = defineEmits<{
    (event: "update:visible", value: boolean): void;
}>();

const activeTabValue = ref<string | number>(PAYLOAD);

function onUpdateVisible(nextVisible: boolean): void {
    emit("update:visible", nextVisible);
}

function onUpdateActiveTab(nextTabValue: string | number): void {
    activeTabValue.value = nextTabValue;
}
</script>

<template>
    <Dialog
        :visible="visible"
        :modal="true"
        :draggable="false"
        :resizable="true"
        :dismissable-mask="true"
        :style="{
            maxWidth: '100vw',
        }"
        :header="$gettext('Analyze payload')"
        @update:visible="onUpdateVisible"
    >
        <div class="payload-analyzer">
            <Tabs
                :value="activeTabValue"
                class="payload-analyzer-tabs"
                @update:value="onUpdateActiveTab"
            >
                <TabList>
                    <Tab :value="PAYLOAD">
                        {{ $gettext("Payload") }}
                    </Tab>
                    <Tab :value="SQL">
                        {{ $gettext("SQL") }}
                    </Tab>
                    <Tab :value="NARRATION">
                        {{ $gettext("Narration") }}
                    </Tab>
                </TabList>

                <TabPanels class="payload-analyzer-tabpanels">
                    <TabPanel value="payload">
                        <PayloadAnalyzerPayloadPanel :payload="payload" />
                    </TabPanel>

                    <TabPanel value="sql">
                        <PayloadAnalyzerSQLPanel :payload="payload" />
                    </TabPanel>

                    <TabPanel value="narration">
                        <PayloadAnalyzerNarrationPanel
                            :payload="payload"
                            :graphs="graphs"
                            :datatypes-to-advanced-search-facets="
                                datatypesToAdvancedSearchFacets
                            "
                        />
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
