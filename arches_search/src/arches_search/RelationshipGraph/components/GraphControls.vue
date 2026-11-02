<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

const { isFullscreen, isFullscreenSupported, canFit } = defineProps<{
    isFullscreen: boolean;
    isFullscreenSupported: boolean;
    canFit: boolean;
}>();

const emit = defineEmits<{
    (event: "close"): void;
    (event: "toggle-fullscreen"): void;
    (event: "fit"): void;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <div class="graph-controls">
        <Button
            class="control"
            variant="outlined"
            severity="secondary"
            icon="pi pi-times"
            :aria-label="$gettext('Close the graph')"
            :title="$gettext('Close the graph')"
            @click="emit('close')"
        />
        <Button
            v-if="isFullscreenSupported"
            class="control"
            variant="outlined"
            severity="secondary"
            :icon="
                isFullscreen ? 'pi pi-window-minimize' : 'pi pi-window-maximize'
            "
            :aria-label="
                isFullscreen
                    ? $gettext('Exit full screen')
                    : $gettext('Show the graph full screen')
            "
            :title="
                isFullscreen
                    ? $gettext('Exit full screen')
                    : $gettext('Show the graph full screen')
            "
            :aria-pressed="isFullscreen"
            @click="emit('toggle-fullscreen')"
        />
        <Button
            class="control"
            variant="outlined"
            severity="secondary"
            icon="pi pi-arrows-alt"
            :disabled="!canFit"
            :aria-label="$gettext('Fit the graph to the panel')"
            :title="$gettext('Fit the graph to the panel')"
            @click="emit('fit')"
        />
    </div>
</template>

<style scoped>
.graph-controls {
    position: absolute;
    inset-block-start: 0.8rem;
    inset-inline-end: 0.8rem;
    z-index: 3;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}

.graph-controls .control.p-button {
    inline-size: 4rem;
    block-size: 4rem;
    /* Outlined buttons are see-through, which would show the graph behind them */
    background: var(--arches-search-card-bg);
}

.graph-controls .control.p-button :deep(.p-button-icon) {
    font-size: 1.8rem;
}
</style>
