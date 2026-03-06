<script setup lang="ts">
import { ref } from "vue";

const topPanelEl = ref<HTMLElement | null>(null);
const topPanelHeight = ref("auto");

const isDragging = ref(false);

let startY = 0;
let startHeight = 0;
let containerHeight = 0;
let maxPercentage = 100;

function onPointerDown(event: PointerEvent) {
    const gutter = event.currentTarget as HTMLElement;
    const topPanel = topPanelEl.value;
    const container = gutter.parentElement;
    if (!topPanel || !container) return;

    const bottomMin =
        parseFloat(
            getComputedStyle(gutter.nextElementSibling as HTMLElement)
                .minHeight,
        ) || 0;

    startY = event.clientY;
    startHeight = topPanel.offsetHeight;
    containerHeight = container.offsetHeight;
    maxPercentage =
        ((containerHeight - gutter.offsetHeight - bottomMin) /
            containerHeight) *
        100;

    gutter.setPointerCapture(event.pointerId);
    isDragging.value = true;
}

function onPointerMove(event: PointerEvent) {
    if (!isDragging.value) return;
    const heightPercentage =
        ((startHeight + event.clientY - startY) / containerHeight) * 100;
    topPanelHeight.value = `${Math.max(0, Math.min(maxPercentage, heightPercentage))}%`;
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
    overflow: auto;
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
