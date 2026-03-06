<script setup lang="ts">
import { ref, computed, watch, watchEffect } from "vue";

import VirtualScroller from "primevue/virtualscroller";

const SCROLL_THRESHOLD_ITEMS = 2;

const { items, isSearching, hasNextPage } = defineProps<{
    items: unknown[];
    isSearching: boolean;
    hasNextPage: boolean;
}>();

const emit = defineEmits<{
    "request-page": [];
}>();

const itemHeight = ref(0);
const itemContainerRef = ref<HTMLElement | null>(null);
const isPageRequestInFlight = ref(false);

const effectiveItemHeight = computed(() => itemHeight.value || 100);

watchEffect(
    (onCleanup) => {
        if (!itemContainerRef.value) {
            return;
        }

        const observer = new ResizeObserver((entries) => {
            const height = entries[0]?.borderBoxSize[0]?.blockSize;
            if (height) {
                itemHeight.value = height;
            }
        });

        observer.observe(itemContainerRef.value);
        onCleanup(() => observer.disconnect());
    },
    { flush: "post" },
);

watch(
    () => isSearching,
    (isNowSearching) => {
        if (!isNowSearching) {
            isPageRequestInFlight.value = false;
        }
    },
);

function handleScroll(event: Event) {
    const container = event.target as HTMLElement | null;
    if (!container || !itemHeight.value) {
        return;
    }

    const distanceFromBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight;

    if (distanceFromBottom > itemHeight.value * SCROLL_THRESHOLD_ITEMS) {
        return;
    }

    if (isSearching || isPageRequestInFlight.value || !hasNextPage) {
        return;
    }

    isPageRequestInFlight.value = true;
    emit("request-page");
}
</script>

<template>
    <VirtualScroller
        :items="items"
        :item-size="effectiveItemHeight"
        :append-only="true"
        :show-loader="false"
        :loading="isSearching"
        @scroll.passive="handleScroll"
    >
        <template #item="{ item }">
            <div ref="itemContainerRef">
                <slot
                    name="item"
                    :item="item"
                />
            </div>
        </template>
    </VirtualScroller>
</template>
