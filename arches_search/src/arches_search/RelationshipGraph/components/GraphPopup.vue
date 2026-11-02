<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { placePopup } from "@/arches_search/RelationshipGraph/utils/popup-position.ts";

import type { Size } from "@/arches_search/RelationshipGraph/utils/popup-position.ts";

const POPUP_MARGIN = 8;

const { anchorX, anchorY, clearance, stageWidth, stageHeight, label } =
    defineProps<{
        anchorX: number;
        anchorY: number;
        clearance: number;
        stageWidth: number;
        stageHeight: number;
        label: string;
    }>();

const emit = defineEmits<{
    (event: "close"): void;
}>();

const { $gettext } = useGettext();

const popupElement = ref<HTMLDivElement | null>(null);
const popupSize = ref<Size | null>(null);

let resizeObserver: ResizeObserver | null = null;

// Not known until the popup has been drawn, so it is hidden until then
const placement = computed(() =>
    popupSize.value
        ? placePopup(
              { x: anchorX, y: anchorY },
              clearance,
              popupSize.value,
              { width: stageWidth, height: stageHeight },
              POPUP_MARGIN,
          )
        : null,
);

onMounted(() => {
    if (!popupElement.value) return;

    measure();
    resizeObserver = new ResizeObserver(measure);
    resizeObserver.observe(popupElement.value);
});

onBeforeUnmount(() => {
    resizeObserver?.disconnect();
});

function measure(): void {
    if (!popupElement.value) return;
    popupSize.value = {
        width: popupElement.value.offsetWidth,
        height: popupElement.value.offsetHeight,
    };
}
</script>

<template>
    <div
        ref="popupElement"
        class="graph-popup"
        role="dialog"
        :aria-label="label"
        :style="{
            // Physical on purpose: these are the canvas's own coordinates
            left: `${placement?.x ?? 0}px`,
            top: `${placement?.y ?? 0}px`,
            visibility: placement ? 'visible' : 'hidden',
        }"
    >
        <Button
            class="close"
            variant="text"
            size="small"
            icon="pi pi-times"
            :aria-label="$gettext('Close')"
            :title="$gettext('Close')"
            @click="emit('close')"
        />
        <slot />
    </div>
</template>

<style scoped>
.graph-popup {
    position: absolute;
    z-index: 2;
    box-sizing: border-box;
    inline-size: max-content;
    max-inline-size: 30rem;
    padding: 1.2rem 1.4rem;
    border: 0.0625rem solid var(--p-content-border-color);
    border-radius: 0.8rem;
    background: var(--arches-search-card-bg);
    box-shadow: var(--arches-search-card-shadow-hover);
}

.graph-popup .close {
    position: absolute;
    inset-block-start: 0.4rem;
    inset-inline-end: 0.4rem;
}
</style>
