<script setup lang="ts">
import { computed, ref } from "vue";

import { useRouter } from "vue-router";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import {
    DARK_MODE_CLASS,
    DARK_MODE_STORAGE_KEY,
} from "@/arches_search/default_theme.ts";
import { routeNames } from "@/arches_search/routes.ts";

defineProps<{
    eyebrow: string | null;
    title: string | null;
    subtitle: string | null;
}>();

const { $gettext } = useGettext();
const router = useRouter();

const isDarkMode = ref(
    document.documentElement.classList.contains(DARK_MODE_CLASS),
);

const darkModeToggleAriaLabel = computed<string>(() => {
    let ariaLabel = $gettext("Switch to dark mode");
    if (isDarkMode.value) {
        ariaLabel = $gettext("Switch to light mode");
    }
    return ariaLabel;
});

const darkModeToggleTitle = computed<string>(() => {
    let title = $gettext("Dark mode");
    if (isDarkMode.value) {
        title = $gettext("Light mode");
    }
    return title;
});

function onToggleDarkMode(): void {
    isDarkMode.value = !isDarkMode.value;
    document.documentElement.classList.toggle(
        DARK_MODE_CLASS,
        isDarkMode.value,
    );
    localStorage.setItem(DARK_MODE_STORAGE_KEY, String(isDarkMode.value));
}

function onNavigateToAdvancedSearch(): void {
    router.push({ name: routeNames.advancedSearch });
}
</script>

<template>
    <header class="search-landing-hero">
        <div class="hero-band">
            <Button
                icon="pi pi-sliders-h"
                icon-pos="left"
                class="hero-adv-link"
                :label="$gettext('Advanced search')"
                :text="true"
                @click="onNavigateToAdvancedSearch"
            />

            <Button
                class="hero-dark-toggle"
                :icon="isDarkMode ? 'pi pi-sun' : 'pi pi-moon'"
                :title="darkModeToggleTitle"
                :aria-label="darkModeToggleAriaLabel"
                :text="true"
                @click="onToggleDarkMode"
            />

            <div class="hero-inner">
                <p
                    v-if="eyebrow"
                    class="hero-eyebrow"
                >
                    {{ eyebrow }}
                </p>
                <h1
                    v-if="title"
                    class="hero-title"
                >
                    {{ title }}
                </h1>
                <p
                    v-if="subtitle"
                    class="hero-subtitle"
                >
                    {{ subtitle }}
                </p>

                <div class="hero-search-bar">
                    <slot />
                </div>

                <div class="hero-search-hint">
                    <Button
                        :label="
                            $gettext('Need more control? Try Advanced search →')
                        "
                        :text="true"
                        @click="onNavigateToAdvancedSearch"
                    />
                </div>
            </div>
        </div>
    </header>
</template>

<style scoped>
.search-landing-hero {
    display: flex;
    flex-direction: column;
    background-color: var(--arches-search-page-bg);
}

.hero-band {
    position: relative;
    overflow: hidden;
    padding: 7rem 2.4rem 7.4rem;
    background: var(--arches-search-hero-gradient);
}

.hero-band::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image: var(--arches-search-hero-dot-grid);
    background-size: var(--arches-search-hero-dot-grid-size);
}

.hero-band::after {
    content: "";
    position: absolute;
    right: var(--arches-search-hero-glow-offset);
    bottom: var(--arches-search-hero-glow-offset);
    inline-size: var(--arches-search-hero-glow-size);
    block-size: var(--arches-search-hero-glow-size);
    background: var(--arches-search-hero-glow);
    pointer-events: none;
}

.hero-inner {
    position: relative;
    z-index: 1;
    max-inline-size: 78rem;
    margin-inline: auto;
    text-align: center;
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    margin: 0 0 1.8rem;
    padding: 0.4rem 1.2rem;
    border: 0.1rem solid var(--arches-search-hero-eyebrow-border);
    border-radius: var(--arches-search-radius-pill);
    background: var(--arches-search-hero-eyebrow-bg);
    color: var(--arches-search-hero-eyebrow-text);
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.088rem;
    text-transform: uppercase;
}

.hero-title {
    margin: 0 0 1.2rem;
    color: var(--arches-search-hero-title-text);
    font-size: 4.2rem;
    font-weight: 800;
    line-height: 1.12;
    letter-spacing: -0.084rem;
}

.hero-subtitle {
    margin: 0 0 1.6rem;
    color: var(--arches-search-hero-subtitle-text);
    font-size: 1.5rem;
}

.hero-search-bar {
    inline-size: 100%;
    max-inline-size: 80rem;
    margin-inline: auto;
}

.hero-search-hint {
    margin-block-start: 1rem;
    text-align: right;
}

.hero-search-hint :deep(.p-button) {
    padding: 0;
    color: var(--arches-search-hero-hint-text);
    font-size: 1.4rem;
    font-weight: 400;
}

.hero-search-hint :deep(.p-button:hover) {
    color: var(--arches-search-hero-hint-text-hover);
    background: transparent;
}

.hero-adv-link.p-button {
    position: absolute;
    z-index: 10;
    inset-block-start: 2rem;
    inset-inline-start: 2.4rem;
    padding: 0;
    color: var(--arches-search-hero-link-text);
    font-size: 1.4rem;
    font-weight: 400;
}

.hero-adv-link.p-button:hover {
    color: var(--arches-search-hero-link-text-hover);
    background: transparent;
}

.hero-adv-link :deep(.p-button-icon) {
    font-size: 1.3rem;
}

.hero-dark-toggle.p-button {
    position: absolute;
    z-index: 10;
    inset-block-start: 1.6rem;
    inset-inline-end: 2rem;
    padding: 1rem 2rem;
    border: 0.1rem solid var(--arches-search-hero-toggle-border);
    border-radius: 0.8rem;
    background: var(--arches-search-hero-toggle-bg);
    color: var(--arches-search-hero-toggle-text);
    line-height: 1;
}

.hero-dark-toggle :deep(.p-button-icon) {
    font-size: 1.8rem;
}

.hero-dark-toggle.p-button:hover {
    background: var(--arches-search-hero-toggle-bg-hover);
    color: var(--arches-search-hero-title-text);
}
</style>
