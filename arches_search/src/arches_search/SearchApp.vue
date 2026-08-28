<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import Button from "primevue/button";
import Card from "primevue/card";

import { routeNames } from "@/arches_search/routes.ts";
import { usePendingSearchStore } from "@/arches_search/stores/usePendingSearchStore.ts";

const router = useRouter();
const route = useRoute();

router.afterEach((to, _from, failure) => {
    if (to.name !== routeNames.simpleSearch || failure) {
        usePendingSearchStore().clear();
    }
});

const isSearchLanding = computed(() => route.name === routeNames.searchLanding);
const isSimpleSearch = computed(() => route.name === routeNames.simpleSearch);
</script>

<template>
    <Card
        :class="{
            'search-card': !isSearchLanding,
            'search-landing-card': isSearchLanding,
        }"
    >
        <template #header>
            <header
                v-if="!isSearchLanding"
                class="simple-search-header"
            >
                <h1 class="search-title">
                    <i class="pi pi-search" />
                    {{ $gettext("Search the Collection") }}
                </h1>
                <nav
                    v-if="isSimpleSearch"
                    class="header-nav"
                >
                    <Button
                        icon="pi pi-sliders-h"
                        icon-pos="left"
                        class="header-link"
                        :label="$gettext('Advanced Search')"
                        :text="true"
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
                        icon="pi pi-sliders-h"
                        icon-pos="left"
                        class="header-link"
                        :label="$gettext('Simple Search')"
                        :text="true"
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
    box-shadow: var(--arches-search-card-shadow);
}

.search-landing-card {
    display: flex;
    flex-direction: column;
    block-size: 100%;
    overflow-y: auto;
    border-radius: 0;
    background-color: var(--arches-search-page-bg);
}

.simple-search-header {
    display: flex;
    flex-shrink: 0;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 1.6rem;
    padding: 2rem 2rem 0.4rem;
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
    letter-spacing: -0.044rem;
}

.search-title .pi {
    font-size: 1.8rem;
    color: var(--p-primary-color);
}

.search-card :deep(.p-card-body),
.search-landing-card :deep(.p-card-body) {
    display: flex;
    flex-direction: column;
    flex: 1;
    padding: 0;
}

.search-card :deep(.p-card-content),
.search-landing-card :deep(.p-card-content) {
    flex: 1;
}

.search-card :deep(.p-card-body) {
    min-block-size: 0;
    overflow-x: hidden;
    overflow-y: hidden;
}

.search-card :deep(.p-card-content) {
    min-block-size: 0;
}

.header-nav {
    display: flex;
    gap: 1.6rem;
}

.header-link {
    padding: 0.5rem 1.2rem;
    color: var(--p-highlight-color);
    border-radius: var(--arches-search-radius-pill);
    background: var(--p-highlight-background);
    font-size: 1.2rem;
    font-weight: 600;
    white-space: nowrap;
    transition:
        background 0.15s,
        color 0.15s;
}

.header-link:hover {
    background: var(--p-highlight-focus-background);
    color: var(--p-highlight-focus-color);
}
</style>
