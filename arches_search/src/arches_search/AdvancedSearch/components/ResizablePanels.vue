<script setup lang="ts">
import { ref } from "vue";

const topPanelEl = ref<HTMLElement | null>(null);
const topPanelHeight = ref("auto");

const isDragging = ref(false);

let startClientY = 0;
let startTopPanelHeightPixels = 0;
let containerHeightPixels = 0;
let maxTopPanelPercent = 100;

function onPointerDown(event: PointerEvent) {
    const gutterElement = event.currentTarget as HTMLElement;
    const topPanelElement = topPanelEl.value;
    const containerElement = gutterElement.parentElement;
    const bottomPanelElement = gutterElement.nextElementSibling;

    if (!topPanelElement || !containerElement) return;

    const bottomPanelMinHeightPixels =
        parseFloat(
            bottomPanelElement
                ? getComputedStyle(bottomPanelElement).minHeight
                : "0",
        ) || 0;

    containerHeightPixels = containerElement.offsetHeight;
    maxTopPanelPercent =
        ((containerHeightPixels -
            gutterElement.offsetHeight -
            bottomPanelMinHeightPixels) /
            containerHeightPixels) *
        100;

    startClientY = event.clientY;
    startTopPanelHeightPixels = topPanelElement.offsetHeight;

    gutterElement.setPointerCapture(event.pointerId);
    isDragging.value = true;
}

function onPointerMove(event: PointerEvent) {
    if (!isDragging.value) return;

    const newTopPanelHeightPixels =
        startTopPanelHeightPixels + (event.clientY - startClientY);
    const newTopPanelPercent =
        (newTopPanelHeightPixels / containerHeightPixels) * 100;

    topPanelHeight.value = `${Math.max(0, Math.min(maxTopPanelPercent, newTopPanelPercent))}%`;
}

function onPointerUp() {
    isDragging.value = false;
}
</script>

<template>
    <div
        class="resizable-panels"
        :class="{ 'is-dragging': isDragging }"
    >
        <div
            ref="topPanelEl"
            class="top-panel"
        >
            <slot name="top" />
        </div>

        <div
            class="gutter"
            role="separator"
            aria-orientation="horizontal"
            @pointerdown="onPointerDown"
            @pointermove="onPointerMove"
            @pointerup="onPointerUp"
        >
            <div class="gutter-handle" />
        </div>

        <div class="bottom-panel">
            <slot name="bottom" />
        </div>
    </div>
</template>

<style scoped>
.resizable-panels {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.top-panel {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    overflow: hidden;
    height: v-bind(topPanelHeight);
}

.gutter {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 0.75rem;
    cursor: row-resize;
    background: var(--p-content-border-color);
}

.gutter-handle {
    width: 3rem;
    height: 0.4rem;
    border-radius: 0.4rem;
    background: var(--p-surface-500);
}

.bottom-panel {
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow: hidden;
}

.is-dragging {
    cursor: row-resize;
    user-select: none;
}
</style>
