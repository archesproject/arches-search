<script setup lang="ts">
import { ref, computed, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Card from "primevue/card";

import arches from "arches";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";
import { getThumbnailExists } from "@/arches_search/AdvancedSearch/api.ts";

import type { ResourceData } from "@/arches_search/AdvancedSearch/types.ts";

type ResourceDescriptor = {
    name?: string;
    description?: string;
    [key: string]: unknown;
};

const { result } = defineProps<{
    result: ResourceData;
}>();

const { $gettext } = useGettext();

const resourceLink = ref<string>("");
const resourceDisplayName = ref<string>("");
const resourceDescriptionText = ref<string>("");

const doesThumbnailExist = ref(false);
const shouldShowMoreDetails = ref(false);

watchEffect(function () {
    const resourceIdentifier = result.resourceinstanceid;

    updateResourceLink(resourceIdentifier);
    updateResourceText();
    void updateThumbnail(resourceIdentifier);
});

const showMoreButtonState = computed(() => {
    if (shouldShowMoreDetails.value) {
        return {
            label: $gettext("Show Less"),
            icon: "pi pi-chevron-down",
        };
    }

    return {
        label: $gettext("Show More"),
        icon: "pi pi-chevron-right",
    };
});

function updateResourceLink(resourceIdentifier: string): void {
    resourceLink.value = generateArchesURL("arches:resource_editor", {
        resourceid: resourceIdentifier,
    });
}

function updateResourceText(): void {
    const descriptorsByLanguage = result.descriptors as
        | Record<string, ResourceDescriptor>
        | undefined;

    const descriptorsForActiveLanguage =
        descriptorsByLanguage?.[arches.activeLanguage];

    resourceDisplayName.value = descriptorsForActiveLanguage?.name ?? "";
    resourceDescriptionText.value =
        descriptorsForActiveLanguage?.description ?? "";
}

async function updateThumbnail(resourceIdentifier: string): Promise<void> {
    try {
        const isThumbnailAvailable =
            await getThumbnailExists(resourceIdentifier);

        if (resourceIdentifier !== result.resourceinstanceid) {
            return;
        }

        doesThumbnailExist.value = isThumbnailAvailable;
    } catch {
        doesThumbnailExist.value = false;
    }
}

function onToggleShowMoreDetails(): void {
    shouldShowMoreDetails.value = !shouldShowMoreDetails.value;
}
</script>

<template>
    <div class="search-result">
        <div
            v-if="doesThumbnailExist"
            class="search-result-thumbnail"
        >
            <img
                :src="`/thumbnail/${result.resourceinstanceid}`"
                :alt="resourceDisplayName"
            />
        </div>

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
                    :icon="showMoreButtonState.icon"
                    :label="showMoreButtonState.label"
                    @click="onToggleShowMoreDetails"
                />
                <Button
                    as="a"
                    icon="pi pi-wrench"
                    target="_blank"
                    size="large"
                    variant="link"
                    :href="resourceLink"
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
    margin: 0 0 0.5rem;
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
    border: 1px solid var(--p-surface-300);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.search-result-thumbnail img {
    max-width: 100%;
    max-height: 100%;
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

.search-result-actions :deep(a) {
    text-decoration: none;
}

.search-result-more {
    margin-top: 1rem;
}

.search-result-more-card {
    width: 100%;
}
</style>
