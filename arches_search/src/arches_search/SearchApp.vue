<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import Card from "primevue/card";

import { routeNames } from "@/arches_search/routes.ts";

const router = useRouter();
const route = useRoute();

const isSimpleSearch = computed(() => route.name === routeNames.simpleSearch);
</script>

<template>
    <Card class="search-card">
        <template #header>
            <header class="simple-search-header">
                <h1 class="search-title">
                    {{ $gettext("Search the Collection") }}
                </h1>
                <nav
                    v-if="isSimpleSearch"
                    class="header-nav"
                >
                    <button
                        class="header-link"
                        @click="
                            router.push({ name: routeNames.advancedSearch })
                        "
                    >
                        <i class="pi pi-sliders-h" />
                        {{ $gettext("Advanced Search") }}
                    </button>
                </nav>
                <nav
                    v-else
                    class="header-nav"
                >
                    <button
                        class="header-link"
                        @click="router.push({ name: routeNames.simpleSearch })"
                    >
                        <i class="pi pi-sliders-h" />
                        {{ $gettext("Simple Search") }}
                    </button>
                </nav>
            </header>
        </template>
        <template #content>
            <router-view />
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
