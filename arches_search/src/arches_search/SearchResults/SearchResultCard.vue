<script setup lang="ts">
import {
    computed,
    nextTick,
    provide,
    ref,
    toRef,
    watch,
    watchEffect,
} from "vue";
import { useGettext } from "vue3-gettext";

import arches from "arches";

import { importComponents } from "@/arches_modular_reports/ModularReport/utils.ts";
import ExpandedResultSection from "@/arches_search/SearchResults/components/ExpandedResultSection.vue";

import type { ComponentLookup } from "@/arches_modular_reports/ModularReport/types.ts";
import type {
    GraphModel,
    ResourceData,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    ResourceDescriptorData,
    ResourceInstanceLifecycleState,
    SearchReportConfig,
} from "@/arches_search/SearchResults/types.ts";

const FALLBACK_THUMB_ICON = "pi pi-box";
const FALLBACK_THUMB_ACCENT_COLOR = "var(--p-surface-500)";

const { $gettext } = useGettext();

const props = defineProps<{
    result: ResourceData;
    descriptorData: ResourceDescriptorData | null;
    reportConfig: SearchReportConfig | null;
    reportConfigLoaded: boolean;
    graphModel: GraphModel | null;
    lifecycleState: ResourceInstanceLifecycleState | null;
}>();

const componentLookup: ComponentLookup = {};

const isExpanded = ref(false);

provide("resourceInstanceId", props.result.resourceinstanceid);
provide("descriptorData", toRef(props, "descriptorData"));
provide("lifecycleState", toRef(props, "lifecycleState"));
provide("searchResultExpanded", isExpanded);

// Read-only stubs for DataSection edit-path injections.
// DataSection destructures these without null guards, so they must be provided.
provide("userCanEditResourceInstance", ref(false));
provide("createTile", {
    createTileRequestId: ref(0),
    createTileRequestedNodegroupAlias: ref(null),
    createTileRequestedTilePath: ref(null),
    requestCreateTile: () => {},
});
provide("softDeleteTile", {
    softDeleteTileRequestId: ref(0),
    softDeleteRequestedNodegroupAlias: ref(null),
    softDeleteRequestedTileId: ref(null),
    requestSoftDeleteTile: () => {},
});
provide("selectedNodegroupAlias", {
    selectedNodegroupAlias: ref(null),
    setSelectedNodegroupAlias: () => {},
});
provide("selectedNodeAlias", {
    selectedNodeAlias: ref(null),
    setSelectedNodeAlias: () => {},
});
provide("selectedTileId", {
    selectedTileId: ref(null),
    setSelectedTileId: () => {},
});
provide("selectedTilePath", {
    selectedTilePath: ref(null),
    setSelectedTilePath: () => {},
});
provide("shouldShowEditor", {
    shouldShowEditor: ref(false),
    setShouldShowEditor: () => {},
});

const configAsNamedSection = computed(() => ({
    name: props.reportConfig?.name ?? "",
    components: props.reportConfig?.components ?? [],
}));

watchEffect(() => {
    if (props.reportConfig?.components?.length) {
        importComponents([configAsNamedSection.value], componentLookup);
    }
});

const thumbIconClass = computed<string>(
    () => props.graphModel?.iconclass || FALLBACK_THUMB_ICON,
);

const thumbLabel = computed<string>(() => props.graphModel?.name ?? "");

const thumbAccentColor = computed<string>(
    () => props.graphModel?.color || FALLBACK_THUMB_ACCENT_COLOR,
);

const shouldShowThumbnailImage = computed<boolean>(
    () =>
        configAsNamedSection.value.components[0]?.config
            ?.show_thumbnail_image === true,
);

const resourceDisplayName = computed<string>(
    () =>
        props.descriptorData?.descriptors?.[arches.activeLanguage]?.name ||
        $gettext("Unnamed Resource"),
);

const hasLoadedThumbnailImage = ref(false);
const thumbnailContainerElement = ref<HTMLDivElement | null>(null);
let hasAttemptedThumbnailLoad = false;

watch(
    () => props.reportConfigLoaded,
    function loadThumbnailImage(isReportConfigLoaded) {
        if (
            !isReportConfigLoaded ||
            hasAttemptedThumbnailLoad ||
            !shouldShowThumbnailImage.value
        ) {
            return;
        }
        hasAttemptedThumbnailLoad = true;

        const thumbnailImageElement = new window.Image();

        thumbnailImageElement.alt = resourceDisplayName.value;
        thumbnailImageElement.className = "search-result-card-thumbnail-image";

        thumbnailImageElement.onload = async function () {
            hasLoadedThumbnailImage.value = true;

            await nextTick();

            if (thumbnailContainerElement.value) {
                thumbnailContainerElement.value.appendChild(
                    thumbnailImageElement,
                );
            }
        };

        thumbnailImageElement.onerror = function () {
            hasLoadedThumbnailImage.value = false;
        };

        thumbnailImageElement.src = `/thumbnail/${props.result.resourceinstanceid}`;
    },
    { immediate: true },
);
</script>

<template>
    <div class="search-result-card">
        <div
            class="search-result-card-thumb"
            :style="{ '--thumb-accent-color': thumbAccentColor }"
        >
            <div
                v-if="shouldShowThumbnailImage && hasLoadedThumbnailImage"
                ref="thumbnailContainerElement"
                class="search-result-card-thumbnail-image-slot"
            ></div>
            <div class="search-result-card-thumb-caption">
                <i :class="[thumbIconClass, 'search-result-card-thumb-icon']" />
                <span
                    v-if="thumbLabel"
                    class="search-result-card-thumb-label"
                    >{{ thumbLabel }}</span
                >
            </div>
        </div>

        <div class="search-result-card-body">
            <component
                :is="componentLookup[component.component]?.component"
                v-for="component in configAsNamedSection.components"
                :key="componentLookup[component.component]?.key"
                :component
                :resource-instance-id="result.resourceinstanceid"
            />
            <ExpandedResultSection />
        </div>
    </div>
</template>

<style scoped>
.search-result-card {
    /* overflow:hidden below makes flex's auto min-height resolve to 0
       instead of content size, so without flex-shrink:0 the card gets
       squished (and its content clipped) inside the scrolling list. */
    display: flex;
    align-items: stretch;
    flex-shrink: 0;
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.8rem;
    background: var(--arches-search-card-bg);
    overflow: hidden;
    cursor: pointer;
    transition:
        box-shadow 0.15s,
        border-color 0.15s;
}

.search-result-card:hover {
    box-shadow:
        0 0.4rem 1.2rem rgba(0, 0, 0, 0.09),
        0 0.2rem 0.4rem rgba(0, 0, 0, 0.05);
    border-color: var(--p-primary-color);
}

.search-result-card-body {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
}

.search-result-card-thumb {
    width: 7.5rem;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 1.2rem 0.6rem;
    background-color: color-mix(
        in srgb,
        var(--thumb-accent-color) 12%,
        var(--arches-search-card-bg)
    );
    border-inline-end: 0.1rem solid var(--p-content-border-color);
}

.search-result-card-thumbnail-image-slot {
    flex: 1;
    width: 100%;
    min-height: 0;
    overflow: hidden;
}

.search-result-card-thumbnail-image-slot
    :deep(.search-result-card-thumbnail-image) {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.search-result-card-thumb-caption {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
    text-align: center;
}

.search-result-card-thumb-icon {
    font-size: 2.2rem;
    color: var(--thumb-accent-color);
}

.search-result-card-thumb-label {
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.036rem;
    color: var(--thumb-accent-color);
    line-height: 1.3;
}
</style>
