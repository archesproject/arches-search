<script setup lang="ts">
import { ref } from "vue";

import Card from "primevue/card";

import AdvancedSearch from "@/arches_search/AdvancedSearch/AdvancedSearch.vue";
import SimpleSearch from "@/arches_search/SimpleSearch/SimpleSearch.vue";

const SIMPLE = "simple";
const ADVANCED = "advanced";
type SearchView = typeof SIMPLE | typeof ADVANCED;

const activeView = ref<SearchView>(SIMPLE);
</script>

<template>
    <Card class="search-card">
        <template #header>
            <header class="simple-search-header">
                <h1 class="search-title">
                    {{ $gettext("Search the Collection") }}
                </h1>
                <nav
                    v-if="activeView === SIMPLE"
                    class="header-nav"
                >
                    <button
                        class="header-link"
                        @click="activeView = ADVANCED"
                    >
                        <i class="pi pi-sliders-h" />
                        {{ $gettext("Advanced Search") }}
                    </button>
                </nav>
                <nav
                    v-if="activeView === ADVANCED"
                    class="header-nav"
                >
                    <button
                        class="header-link"
                        @click="activeView = SIMPLE"
                    >
                        <i class="pi pi-sliders-h" />
                        {{ $gettext("Simple Search") }}
                    </button>
                </nav>
            </header>
        </template>
        <template #content>
            <SimpleSearch v-if="activeView === SIMPLE" />
            <AdvancedSearch v-else />
        </template>
    </Card>
</template>

<style scoped>
.search-card {
    border: none;
    border-radius: 0;
    box-shadow: none;
    height: 100%;
}

.simple-search-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    background-color: var(--p-content-background);
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.search-title {
    font-size: 2rem;
    font-weight: 600;
    margin: 0;
}

:deep(.p-card-body) {
    flex: 1;
    padding: 0;
    overflow-y: hidden;
}

:deep(.p-card-content) {
    height: 100%;
}

.header-nav {
    display: flex;
    gap: 1.6rem;
}

.header-link {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: var(--p-arches-search-font-size);
    text-decoration: none;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    font-family: inherit;
}

.header-link:hover {
    text-decoration: underline;
}
</style>
