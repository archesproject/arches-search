<script setup lang="ts">
import Button from "primevue/button";

import type { ResourceType } from "@/arches_search/SimpleSearch/types.ts";

defineProps<{
    resourceTypes: ResourceType[];
    activeTypeId: string | null;
}>();

defineEmits<{
    (event: "select", typeId: string | null): void;
}>();
</script>

<template>
    <div class="resource-type-filter">
        <Button
            v-for="type in resourceTypes"
            :key="type.id ?? '__all__'"
            :label="type.label"
            :icon="type.icon"
            icon-pos="left"
            size="large"
            severity="secondary"
            variant="outlined"
            :class="['type-btn', { active: activeTypeId === type.id }]"
            @click="$emit('select', type.id)"
        />
    </div>
</template>

<style scoped>
.resource-type-filter {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    padding: 0.8rem 1.6rem;
    background-color: var(--p-content-background);
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.type-btn {
    font-size: var(--p-arches-search-font-size);
}

.type-btn.active,
.type-btn.active:hover,
.p-button-outlined.p-button-secondary.type-btn:hover {
    background-color: var(--p-button-primary-background);
}
</style>
