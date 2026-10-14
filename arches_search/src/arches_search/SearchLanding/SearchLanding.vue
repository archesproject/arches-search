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

const isActiveTabFullWidth = computed<boolean>(
    () =>
        tabs.find((tab) => tab.slug === activeTabSlug.value)?.isFullWidth ===
        true,
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

        <div
            class="search-landing-tab-section"
            :class="{
                'search-landing-tab-section-full-width': isActiveTabFullWidth,
            }"
        >
            <SearchLandingTabs
                class="search-landing-tab-header"
                :tabs="tabs"
                :model-value="activeTabSlug"
                @update:model-value="onTabSelect"
            />

            <div class="search-landing-tab-panel">
                <KeepAlive>
                    <component :is="activeTabComponent" />
                </KeepAlive>
            </div>
        </div>

        <div
            v-if="
                branding.aboutHeading ||
                (branding.aboutBody && branding.aboutBody.length > 0)
            "
            class="search-landing-content"
        >
            <section class="search-landing-about">
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

.search-landing-tab-section {
    display: flex;
    flex-direction: column;
    gap: 2.4rem;
    inline-size: 100%;
    max-inline-size: 120rem;
    margin-inline: auto;
    padding-block: 3.2rem 4.8rem;
    padding-inline: 2rem;
}

.search-landing-tab-section-full-width {
    position: relative;
    max-inline-size: none;
    padding-block-start: 0;
    padding-inline: 0;
}

.search-landing-tab-section-full-width .search-landing-tab-header {
    position: absolute;
    inset-block-start: 0;
    inset-inline: 2rem;
    z-index: 1;
    max-inline-size: 116rem;
    margin-inline: auto;
    padding-block: 1rem;
    padding-inline: 1.4rem;
    border: 0.1rem solid var(--arches-search-card-border);
    border-radius: 0.8rem;
    background: var(--arches-search-card-bg);
    box-shadow: var(--arches-search-floating-header-shadow);
}

.search-landing-tab-panel {
    min-block-size: 48rem;
    isolation: isolate;
}

.search-landing-content {
    max-inline-size: 120rem;
    margin-inline: auto;
    padding-block-end: 4.8rem;
    padding-inline: 2rem;
    inline-size: 100%;
}

.search-landing-about {
    max-inline-size: 70rem;
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
