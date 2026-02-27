<script setup lang="ts">
import { computed, inject, onMounted, nextTick, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import arches from "arches";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

import type { Ref } from "vue";
import type { SectionContent } from "@/arches_modular_reports/ModularReport/types.ts";
import type { ResourceDescriptorData } from "@/arches_search/SearchResults/types.ts";

const { $gettext } = useGettext();

defineProps<{
    component: SectionContent;
}>();

const resourceInstanceId = inject("resourceInstanceId") as string;
const descriptorData = inject("descriptorData") as Ref<
    ResourceDescriptorData | null | undefined
>;

const shouldShowThumbnailContainer = ref(false);
const thumbnailContainerElement = ref<HTMLDivElement | null>(null);
const isExpanded = ref(false);

function toggleExpanded(): void {
    isExpanded.value = !isExpanded.value;
}

const activeDescriptors = computed(function () {
    return descriptorData?.value?.descriptors?.[arches.activeLanguage];
});

const resourceDisplayName = computed<string>(function () {
    return activeDescriptors.value?.name || $gettext("Unnamed Resource");
});

const resourceDescriptionText = computed<string>(function () {
    return activeDescriptors.value?.description || "";
});

const resourceEditorLink = computed<string>(function () {
    return generateArchesURL("arches:resource_editor", {
        resourceid: resourceInstanceId,
    });
});

onMounted(function () {
    if (typeof window === "undefined") {
        return;
    }

    const thumbnailImageElement = new window.Image();

    thumbnailImageElement.alt = resourceDisplayName.value;
    thumbnailImageElement.className = "descriptor-section-thumbnail-image";

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

    thumbnailImageElement.src = `/thumbnail/${resourceInstanceId}`;
});
</script>

<template>
    <div class="descriptor-section">
        <div class="descriptor-section-header">
            <div
                ref="thumbnailContainerElement"
                class="descriptor-section-thumbnail"
            >
                <span
                    v-if="!shouldShowThumbnailContainer"
                    class="descriptor-section-thumbnail-placeholder"
                >
                    {{ $gettext("Image") }}
                </span>
            </div>

            <div class="descriptor-section-content">
                <a
                    :href="resourceEditorLink"
                    target="_blank"
                    class="descriptor-section-title"
                >
                    {{ resourceDisplayName }}
                </a>

                <div class="descriptor-section-actions">
                    <Button
                        :icon="
                            isExpanded
                                ? 'pi pi-chevron-down'
                                : 'pi pi-chevron-right'
                        "
                        variant="link"
                        :label="
                            isExpanded
                                ? $gettext('Show less')
                                : $gettext('Show more')
                        "
                        @click="toggleExpanded"
                    />
                    <Button
                        as="a"
                        icon="pi pi-wrench"
                        target="_blank"
                        variant="link"
                        :href="resourceEditorLink"
                        :label="$gettext('Edit')"
                    />
                    <Button
                        icon="pi pi-sitemap"
                        variant="link"
                        :label="$gettext('Related Resources')"
                    />
                </div>

                <div
                    v-if="resourceDescriptionText"
                    class="descriptor-section-description"
                >
                    <span class="descriptor-section-description-label">
                        {{ $gettext("Description:") }}
                    </span>
                    {{ resourceDescriptionText }}
                </div>
            </div>
        </div>

        <div
            v-if="isExpanded"
            class="descriptor-section-expanded"
        >
            <!-- Config-driven components from report config will render here -->
        </div>
    </div>
</template>

<style scoped>
.descriptor-section {
    --link-color: var(--p-blue-600, #2563eb);

    display: flex;
    flex-direction: column;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.descriptor-section-header {
    display: flex;
    align-items: flex-start;
    gap: 1.5rem;
    padding: 1.5rem 2rem;
}

.descriptor-section-thumbnail {
    width: 10rem;
    height: 10rem;
    flex-shrink: 0;
    background-color: var(--p-surface-100);
    border: 0.125rem solid var(--p-surface-300);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.descriptor-section-thumbnail-placeholder {
    font-size: 1rem;
    color: var(--p-text-muted-color);
}

.descriptor-section-thumbnail-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.descriptor-section-content {
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
    flex: 1;
    min-width: 0;
    padding-top: 0.25rem;
}

.descriptor-section-title {
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--link-color);
    text-decoration: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.descriptor-section-title:hover {
    text-decoration: underline;
}

.descriptor-section-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.descriptor-section-actions :deep(.p-button) {
    font-size: 1.5rem;
    padding-inline: 0;
}

.descriptor-section-actions :deep(.p-button-icon) {
    font-size: 1.25rem;
}

.descriptor-section-description {
    font-size: 1.5rem;
    color: var(--p-text-muted-color);
    line-height: 1.4;
}

.descriptor-section-description-label {
    font-weight: 600;
    color: var(--p-text-color);
    margin-inline-end: 0.25rem;
}

.descriptor-section-expanded {
    border-top: 0.125rem solid var(--p-content-border-color);
    min-height: 8rem;
    background-color: var(--p-content-hover-background);
}
</style>
