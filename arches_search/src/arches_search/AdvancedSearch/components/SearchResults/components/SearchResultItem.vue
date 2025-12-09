<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Card from "primevue/card";

import arches from "arches";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

import type { ResourceData } from "@/arches_search/AdvancedSearch/types.ts";

type ResourceDescriptor = {
    name?: string;
    description?: string;
    [key: string]: unknown;
};

const { $gettext } = useGettext();

const EDIT_BUTTON_LABEL = $gettext("Edit");

const { result } = defineProps<{
    result: ResourceData;
}>();

const shouldShowMoreDetails = ref(false);
const shouldShowThumbnailContainer = ref(false);
const thumbnailContainerElement = ref<HTMLDivElement | null>(null);

const resourceDescriptorsForActiveLanguage = computed<
    ResourceDescriptor | undefined
>(function () {
    return result.descriptors?.[arches.activeLanguage];
});

const resourceLink = computed<string>(function () {
    return generateArchesURL("arches:resource_editor", {
        resourceid: result.resourceinstanceid,
    });
});

const resourceDisplayName = computed<string>(function () {
    return resourceDescriptorsForActiveLanguage.value?.name || "";
});

const resourceDescriptionText = computed<string>(function () {
    return resourceDescriptorsForActiveLanguage.value?.description || "";
});

const showMoreButtonLabel = computed<string>(function () {
    if (shouldShowMoreDetails.value) {
        return $gettext("Show Less");
    }

    return $gettext("Show More");
});

const showMoreButtonIcon = computed<string>(function () {
    if (shouldShowMoreDetails.value) {
        return "pi pi-chevron-down";
    }

    return "pi pi-chevron-right";
});

function onToggleShowMoreDetails(): void {
    shouldShowMoreDetails.value = !shouldShowMoreDetails.value;
}

onMounted(function () {
    if (typeof window === "undefined") {
        return;
    }

    const thumbnailImageElement = new window.Image();

    thumbnailImageElement.alt = resourceDisplayName.value;
    thumbnailImageElement.className = "search-result-thumbnail-image";

    thumbnailImageElement.onload = async function () {
        shouldShowThumbnailContainer.value = true;

        await nextTick();

        if (thumbnailContainerElement.value) {
            thumbnailContainerElement.value.appendChild(thumbnailImageElement);
        }
    };

    thumbnailImageElement.onerror = function () {
        shouldShowThumbnailContainer.value = false;
    };

    thumbnailImageElement.src = `/thumbnail/${result.resourceinstanceid}`;
});
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
                    v-if="resourceLink"
                    :href="resourceLink"
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
                    :href="resourceLink"
                    :label="EDIT_BUTTON_LABEL"
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
