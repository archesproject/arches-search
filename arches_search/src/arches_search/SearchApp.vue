<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";
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
                    <i class="pi pi-search" />
                    {{ $gettext("Search the Collection") }}
                </h1>
                <nav
                    v-if="isSimpleSearch"
                    class="header-nav"
                >
                    <Button
                        :label="$gettext('Advanced Search')"
                        icon="pi pi-sliders-h"
                        icon-pos="left"
                        text
                        class="header-link"
                        @click="
                            router.push({ name: routeNames.advancedSearch })
                        "
                    />
                </nav>
                <nav
                    v-else
                    class="header-nav"
                >
                    <Button
                        :label="$gettext('Simple Search')"
                        icon="pi pi-sliders-h"
                        icon-pos="left"
                        text
                        class="header-link"
                        @click="router.push({ name: routeNames.simpleSearch })"
                    />
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
    padding: 2rem 2rem 0;
    background-color: var(--arches-search-card-bg);
}

.search-title {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 0;
    color: var(--p-text-color);
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}

.search-title .pi {
    font-size: 1.8rem;
    color: var(--p-primary-color);
}

:deep(.p-card-body) {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-block-size: 0;
    padding: 0;
    overflow-x: hidden;
    overflow-y: hidden;
}

:deep(.p-card-content) {
    flex: 1;
    min-block-size: 0;
}

.header-nav {
    display: flex;
    gap: 1.6rem;
}

.header-link {
    padding: 0.5rem 1.2rem;
    color: var(--p-primary-color);
    border: 0.1rem solid var(--p-primary-200);
    border-radius: var(--arches-search-radius-pill);
    background: var(--p-primary-50);
    font-size: 1.2rem;
    font-weight: 600;
    white-space: nowrap;
    transition:
        background 0.15s,
        border-color 0.15s;
}

.header-link:hover {
    border-color: var(--p-primary-300);
    background: var(--p-primary-100);
}
</style>
