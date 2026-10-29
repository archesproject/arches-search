<script setup lang="ts">
import { useGettext } from "vue3-gettext";

defineProps<{
    fromName: string;
    toName: string;
    label: string;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <span class="relationship-sentence">
        <span class="resource">{{ fromName }}</span>
        {{ " " }}
        <span class="relationship-type">
            {{ label || $gettext("Unspecified relationship") }}
        </span>
        {{ " " }}
        <span class="resource">{{ toName }}</span>
    </span>
</template>

<style scoped>
.relationship-sentence {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.6rem;
}

.relationship-sentence .resource {
    font-weight: 600;
    overflow-wrap: anywhere;
}

.relationship-sentence .relationship-type {
    padding: 0.1rem 0.8rem;
    border-radius: var(--arches-search-radius-pill);
    background: var(--arches-search-chip-search-bg);
    color: var(--arches-search-chip-search-text);
    font-size: 1.2rem;
}
</style>
