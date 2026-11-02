import { onBeforeUnmount, onMounted, ref } from "vue";

import type { Ref } from "vue";

// Takes an element to and from full screen. The browser, not the page, decides
// whether it may (it must be asked for by a click, and some embeddings forbid
// it), so `isSupported` says whether to offer it at all.
export function useFullscreen(target: Ref<HTMLElement | null>) {
    const isFullscreen = ref(false);
    const isSupported = document.fullscreenEnabled === true;

    onMounted(() => {
        document.addEventListener("fullscreenchange", onChange);
    });

    onBeforeUnmount(() => {
        document.removeEventListener("fullscreenchange", onChange);
        if (isFullscreenTarget()) void document.exitFullscreen();
    });

    function isFullscreenTarget(): boolean {
        return (
            target.value !== null && document.fullscreenElement === target.value
        );
    }

    // Also how a user leaving with Escape is noticed
    function onChange(): void {
        isFullscreen.value = isFullscreenTarget();
    }

    async function toggle(): Promise<void> {
        if (!target.value) return;

        try {
            if (isFullscreenTarget()) {
                await document.exitFullscreen();
            } else {
                await target.value.requestFullscreen();
            }
        } catch {
            // The browser said no, and there is nothing to be done about that
        }
    }

    return { isFullscreen, isSupported, toggle };
}
