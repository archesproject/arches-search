<script setup lang="ts">
import { ref, computed, watchEffect, nextTick } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Card from "primevue/card";

import arches from "arches";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

import type { ResourceData } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { result } = defineProps<{
    result: ResourceData;
}>();

const shouldShowMoreDetails = ref(false);
const shouldShowThumbnailContainer = ref(false);
const thumbnailContainerElement = ref<HTMLDivElement | null>(null);

const activeLanguageDescriptors = computed(
    () => result.descriptors?.[arches.activeLanguage],
);

const resourceDisplayName = computed(
    () => activeLanguageDescriptors.value?.name ?? "",
);
const resourceDescriptionText = computed(
    () => activeLanguageDescriptors.value?.description ?? "",
);

const resourceEditUrl = computed(() =>
    generateArchesURL("arches:resource_editor", {
        resourceid: result.resourceinstanceid,
    }),
);

const showMoreButtonLabel = computed(() => {
    if (shouldShowMoreDetails.value) {
        return $gettext("Show Less");
    }
    return $gettext("Show More");
});

const showMoreButtonIcon = computed(() => {
    if (shouldShowMoreDetails.value) {
        return "pi pi-chevron-down";
    }
    return "pi pi-chevron-right";
});

watchEffect(
    () => {
        if (typeof window === "undefined") {
            return;
        }

        const thumbnailImage = new window.Image();
        thumbnailImage.alt = resourceDisplayName.value;
        thumbnailImage.className = "search-result-thumbnail-image";

        thumbnailImage.onload = async () => {
            shouldShowThumbnailContainer.value = true;
            await nextTick();
            thumbnailContainerElement.value?.appendChild(thumbnailImage);
        };

        thumbnailImage.onerror = () => {
            shouldShowThumbnailContainer.value = false;
        };

        thumbnailImage.src = `/thumbnail/${result.resourceinstanceid}`;
    },
    { flush: "post" },
);

function onToggleShowMoreDetails() {
    shouldShowMoreDetails.value = !shouldShowMoreDetails.value;
}
</script>

<template>
    <div class="search-result">
        <div
            v-if="shouldShowThumbnailContainer"
            ref="thumbnailContainerElement"
            class="search-result-thumbnail"
        />

        <div class="search-result-content">
            <h1 class="search-result-title">
                <a
                    v-if="resourceEditUrl"
                    :href="resourceEditUrl"
                    target="_blank"
                    rel="noreferrer"
                >
                    {{ resourceDisplayName }}
                </a>
                <span v-else>
                    {{ resourceDisplayName }}
                </span>
            </h1>

            <div
                v-if="resourceDescriptionText"
                class="search-result-description"
            >
                {{ resourceDescriptionText }}
            </div>

            <div class="search-result-actions">
                <Button
                    size="large"
                    variant="text"
                    :icon="showMoreButtonIcon"
                    :label="showMoreButtonLabel"
                    @click="onToggleShowMoreDetails"
                />
                <Button
                    as="a"
                    icon="pi pi-wrench"
                    target="_blank"
                    size="large"
                    variant="link"
                    :href="resourceEditUrl"
                    :label="$gettext('Edit')"
                />
            </div>

            <div
                v-if="shouldShowMoreDetails"
                class="search-result-more"
            >
                <Card class="search-result-more-card">
                    <template #title>
                        {{ $gettext("Hello World Title") }}
                    </template>
                    <template #content>
                        {{ $gettext("Hello world!") }}
                    </template>
                </Card>
            </div>
        </div>
    </div>
</template>

<style scoped>
.search-result {
    display: flex;
    margin: 2rem;
}

.search-result-title {
    font-size: 2rem;
}

.search-result-title > a {
    color: var(--p-primary-color);
    text-decoration: none;
}

.search-result-title > a:hover {
    text-decoration: underline;
}

.search-result-description {
    flex: 1;
    margin-bottom: 1rem;
}

.search-result-thumbnail {
    width: 10rem;
    height: 10rem;
    margin: 0;
    background-color: var(--p-surface-100);
    border: 0.125rem solid var(--p-surface-300);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.search-result-thumbnail-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.search-result-content {
    display: flex;
    flex-direction: column;
    margin: 0 2rem;
    flex: 1;
}

.search-result-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.search-result-more {
    margin-top: 1rem;
}
</style>
