<script setup lang="ts">
import { computed } from "vue";

import Tab from "primevue/tab";
import TabList from "primevue/tablist";
import Tabs from "primevue/tabs";

import type { LandingTab } from "@/arches_search/SearchLanding/types.ts";

const { tabs, modelValue } = defineProps<{
    tabs: LandingTab[];
    modelValue: string;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: string];
}>();

const activeTab = computed<LandingTab | undefined>(() =>
    tabs.find((tab) => tab.slug === modelValue),
);

function onTabSelect(value: string | number): void {
    emit("update:modelValue", String(value));
}
</script>

<template>
    <div class="search-landing-section-header">
        <span
            v-if="activeTab"
            class="search-landing-section-title"
        >
            <i :class="activeTab.icon" />
            <span>{{ activeTab.label }}</span>
        </span>
        <nav class="search-landing-tabs">
            <Tabs
                :value="modelValue"
                @update:value="onTabSelect"
            >
                <TabList>
                    <Tab
                        v-for="tab in tabs"
                        :key="tab.slug"
                        :value="tab.slug"
                    >
                        <i :class="tab.icon" />
                        <span>{{ tab.label }}</span>
                    </Tab>
                </TabList>
            </Tabs>
        </nav>
    </div>
</template>

<style scoped>
.search-landing-section-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-block-end: 1.6rem;
}

.search-landing-section-title {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    gap: 0.7rem;
    color: var(--p-text-color);
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1;
}

.search-landing-section-title .pi {
    color: var(--p-primary-color);
    font-size: 1.4rem;
    position: relative;
    inset-block-start: 0.1rem;
}

.search-landing-tabs {
    margin-inline-start: auto;
    min-inline-size: 0;
}

.search-landing-tabs :deep(.p-tablist) {
    background: transparent;
    border-width: 0;
}

.search-landing-tabs :deep(.p-tablist-tab-list) {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.6rem;
    border: none;
}

.search-landing-tabs :deep(.p-tablist-active-bar) {
    display: none;
}

.search-landing-tabs :deep(.p-tab) {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    padding: 0.5rem 1.3rem;
    border-radius: var(--arches-search-radius-pill);
    font-size: 1.2rem;
    font-weight: 600;
    white-space: nowrap;
    cursor: pointer;
    border: 0.1rem solid var(--arches-search-card-border);
    background: var(--p-content-background);
    color: var(--arches-search-sec-btn-text);
    font-family: inherit;
}

.search-landing-tabs :deep(.p-tab .pi) {
    font-size: 1.1rem;
}

.search-landing-tabs :deep(.p-tab:hover) {
    border-color: var(--p-primary-color);
    background: var(--arches-search-primary-muted-bg);
    color: var(--p-primary-color);
}

.search-landing-tabs :deep(.p-tab:focus-visible) {
    outline: 0.2rem solid var(--p-primary-color);
    outline-offset: 0.2rem;
}

.search-landing-tabs :deep(.p-tab-active) {
    background: var(--p-primary-color);
    border-color: var(--p-primary-color);
    color: var(--p-primary-contrast-color, var(--p-surface-0));
}
</style>
