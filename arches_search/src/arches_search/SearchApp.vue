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
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: 0;
    background-color: var(--arches-search-card-bg);
    box-shadow:
        0 0.1rem 0.3rem rgba(0, 0, 0, 0.06),
        0 0.1rem 0.2rem rgba(0, 0, 0, 0.04);
}

.simple-search-header {
    display: flex;
    flex-shrink: 0;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 1.6rem;
    padding: 2rem 2.4rem;
    background-color: var(--arches-search-card-bg);
    border-bottom: 0.1rem solid var(--p-content-border-color);
}

.search-title {
    margin: 0;
    color: var(--p-text-color);
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
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
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 1.2rem;
    color: var(--p-primary-color);
    border: 0.1rem solid var(--p-primary-200);
    border-radius: 999rem;
    background: var(--p-primary-50);
    font-family: inherit;
    font-size: 1.2rem;
    font-weight: 600;
    text-decoration: none;
    white-space: nowrap;
    cursor: pointer;
    transition:
        background 0.15s,
        border-color 0.15s;
}

.header-link:hover {
    border-color: var(--p-primary-300);
    background: var(--p-primary-100);
}
</style>
