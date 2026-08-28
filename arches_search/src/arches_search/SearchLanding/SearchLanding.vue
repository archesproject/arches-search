<script setup lang="ts">
import { computed, defineAsyncComponent, ref, watchEffect } from "vue";
import { useRouter } from "vue-router";
import { useGettext } from "vue3-gettext";

import SearchLandingHero from "@/arches_search/SearchLanding/components/SearchLandingHero.vue";
import SearchLandingTabs from "@/arches_search/SearchLanding/components/SearchLandingTabs.vue";
import TermSearchInput from "@/arches_search/SimpleSearch/components/TermFilter/TermSearchInput.vue";
import { fetchResourceTypeCounts } from "@/arches_search/SearchLanding/api.ts";
import { useLandingContent } from "@/arches_search/SearchLanding/landing-content.ts";
import { routeNames } from "@/arches_search/routes.ts";
import { usePendingSearchStore } from "@/arches_search/stores/usePendingSearchStore.ts";

import type { Component } from "vue";
import type { TermKind } from "@/arches_search/SimpleSearch/types.ts";

const router = useRouter();
const { interpolate } = useGettext();

const { branding, tabs } = useLandingContent();
const activeTabSlug = ref(tabs[0]?.slug ?? "");
const componentBySlug: Record<string, Component> = Object.fromEntries(
    tabs.map((tab) => [
        tab.slug,
        defineAsyncComponent(() => import(`@/${tab.component}.vue`)),
    ]),
);

const totalResourceCount = ref<number | null>(null);

const resolvedSubtitle = computed<string | null>(() => {
    if (!branding.subtitle) {
        return branding.subtitle;
    }
    if (totalResourceCount.value === null) {
        return branding.subtitle;
    }
    return interpolate(branding.subtitle, {
        total: String(totalResourceCount.value),
    });
});

const activeTabComponent = computed<Component | null>(
    () => componentBySlug[activeTabSlug.value] ?? null,
);

watchEffect(async () => {
    try {
        const counts = await fetchResourceTypeCounts();
        totalResourceCount.value = counts.reduce(
            (sum, entry) => sum + entry.count,
            0,
        );
    } catch (error) {
        console.error(error);
    }
});

function onTabSelect(slug: string): void {
    activeTabSlug.value = slug;
}

function onSearchBarSubmit(payload: {
    text: string;
    termKind?: TermKind;
    icon?: string;
}): void {
    usePendingSearchStore().set({
        term: payload.text,
        ...(payload.termKind ? { termKind: payload.termKind } : {}),
        ...(payload.icon ? { termIcon: payload.icon } : {}),
    });
    router.push({ name: routeNames.simpleSearch });
}
</script>

<template>
    <div class="search-landing">
        <SearchLandingHero
            :eyebrow="branding.eyebrow"
            :title="branding.title"
            :subtitle="resolvedSubtitle"
        >
            <TermSearchInput @submit="onSearchBarSubmit" />
        </SearchLandingHero>

        <div class="search-landing-content">
            <SearchLandingTabs
                :tabs="tabs"
                :model-value="activeTabSlug"
                @update:model-value="onTabSelect"
            />

            <div class="search-landing-tab-panel">
                <KeepAlive>
                    <component :is="activeTabComponent" />
                </KeepAlive>
            </div>

            <section
                v-if="
                    branding.aboutHeading ||
                    (branding.aboutBody && branding.aboutBody.length > 0)
                "
                class="search-landing-about"
            >
                <div class="search-landing-about-header">
                    <i
                        v-if="branding.aboutIcon"
                        :class="branding.aboutIcon"
                    />
                    <h2
                        v-if="branding.aboutHeading"
                        class="search-landing-about-heading"
                    >
                        {{ branding.aboutHeading }}
                    </h2>
                </div>
                <p
                    v-for="(paragraph, paragraphIndex) in branding.aboutBody"
                    :key="paragraphIndex"
                    class="search-landing-about-body"
                >
                    {{ paragraph }}
                </p>
            </section>
        </div>
    </div>
</template>

<style scoped>
.search-landing {
    display: flex;
    flex-direction: column;
    min-block-size: 100%;
}

.search-landing-content {
    max-inline-size: 120rem;
    margin-inline: auto;
    padding-block: 3.2rem 4.8rem;
    padding-inline: 2rem;
    inline-size: 100%;
}

.search-landing-tab-panel {
    min-block-size: 48rem;
    padding-block-start: 0.8rem;
}

.search-landing-about {
    max-inline-size: 70rem;
    margin-block: 4.8rem 0;
    margin-inline: auto;
    padding-block: 2.2rem;
    padding-inline: 2.4rem;
    border: 0.1rem solid var(--arches-search-card-border);
    border-radius: 1.2rem;
    background: var(--arches-search-card-bg);
}

.search-landing-about-header {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin-block-end: 0.6rem;
}

.search-landing-about-header .pi {
    color: var(--p-primary-color);
    font-size: 1.4rem;
}

.search-landing-about-heading {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--p-text-color);
}

.search-landing-about-body {
    margin-block: 0 1.2rem;
    margin-inline: 0;
    font-size: 1.3rem;
    line-height: 1.8;
    color: var(--p-text-muted-color);
}

.search-landing-about-body:last-of-type {
    margin-block-end: 0;
}
</style>
