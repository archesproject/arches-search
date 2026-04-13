<script setup lang="ts">
import { useGettext } from "vue3-gettext";
import Button from "primevue/button";

const { $gettext } = useGettext();

defineProps<{
    disabled: boolean;
    isRoot: boolean;
}>();

const emit = defineEmits<{
    "add-group": [];
    "add-filter": [];
    "add-string-search": [];
    "add-time-filter": [];
    "add-relationship": [];
    "add-map-filter": [];
    "remove-group": [];
}>();
</script>

<template>
    <div class="group-actions">
        <Button
            severity="secondary"
            icon="pi pi-table"
            :label="$gettext('Add group')"
            :disabled="disabled"
            @click.stop="emit('add-group')"
        />
        <Button
            severity="secondary"
            icon="pi pi-filter"
            :label="$gettext('Add filter')"
            :disabled="disabled"
            @click.stop="emit('add-filter')"
        />
        <Button
            severity="secondary"
            icon="pi pi-search"
            :label="$gettext('Add text search')"
            :disabled="disabled"
            @click.stop="emit('add-string-search')"
        />
        <Button
            severity="secondary"
            icon="pi pi-calendar"
            :label="$gettext('Add time filter')"
            :disabled="disabled"
            @click.stop="emit('add-time-filter')"
        />
        <Button
            severity="secondary"
            icon="pi pi-link"
            :label="$gettext('Add relationship filter')"
            :disabled="disabled"
            @click.stop="emit('add-relationship')"
        />
        <Button
            severity="secondary"
            icon="pi pi-map"
            :label="$gettext('Add map filter')"
            :disabled="disabled"
            @click.stop="emit('add-map-filter')"
        />
        <div
            v-if="!isRoot"
            class="group-actions-remove"
        >
            <Button
                severity="danger"
                icon="pi pi-trash"
                variant="outlined"
                :label="$gettext('Remove group')"
                :aria-label="$gettext('Remove group')"
                @click.stop="emit('remove-group')"
            />
        </div>
    </div>
</template>

<style scoped>
.group-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    align-items: center;
}

.group-actions-remove {
    margin-inline-start: auto;
    display: flex;
    flex: 0 0 auto;
}
</style>
