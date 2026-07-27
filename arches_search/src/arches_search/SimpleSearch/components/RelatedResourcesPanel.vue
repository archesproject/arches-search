<script setup lang="ts">
import { useGettext } from "vue3-gettext";

defineProps<{
    resourceTitle: string;
}>();

const emit = defineEmits<{
    (event: "close"): void;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <div class="related-resources-panel">
        <div class="related-resources-header">
            <h3 class="related-resources-title">
                <i class="pi pi-sitemap" />
                {{
                    $gettext("%{title}: related resources", {
                        title: resourceTitle,
                    })
                }}
            </h3>
            <button
                class="related-resources-back-btn"
                @click="emit('close')"
            >
                <i class="pi pi-arrow-left" />
                {{ $gettext("Back") }}
            </button>
        </div>

        <div class="related-resources-placeholder">
            <i class="pi pi-sitemap" />
            <span>{{ $gettext("Related resources — placeholder") }}</span>
        </div>
    </div>
</template>

<style scoped>
.related-resources-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--arches-search-card-bg);
}

.related-resources-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 2rem 2rem 0.75rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.related-resources-title {
    margin: 0;
    display: flex;
    align-items: center;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--p-text-color);
}

.related-resources-title .pi {
    margin-inline-end: 0.6rem;
    color: var(--p-primary-color);
    flex-shrink: 0;
}

.related-resources-back-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    flex-shrink: 0;
    padding: 0.3rem 0.8rem;
    font-family: inherit;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--p-text-muted-color);
    background: none;
    border: none;
    border-radius: 0.4rem;
    cursor: pointer;
}

.related-resources-back-btn:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.related-resources-placeholder {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.2rem;
    color: var(--p-text-muted-color);
}

.related-resources-placeholder .pi {
    font-size: 4.8rem;
    opacity: 0.3;
}

.related-resources-placeholder span {
    font-size: 1.4rem;
}
</style>
