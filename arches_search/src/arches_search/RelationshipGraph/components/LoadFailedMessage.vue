<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

defineProps<{
    message: string;
}>();

const emit = defineEmits<{
    (event: "retry"): void;
}>();

const { $gettext } = useGettext();
</script>

<template>
    <div class="message">
        <span>{{ message }}</span>
        <Button
            variant="link"
            :label="$gettext('Try again')"
            @click="emit('retry')"
        />
    </div>
</template>

<style scoped>
.message {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 1.3rem;
    color: var(--p-text-muted-color);
}
</style>
