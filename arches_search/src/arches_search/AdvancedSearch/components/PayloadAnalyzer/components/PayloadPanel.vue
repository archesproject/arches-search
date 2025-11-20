<script setup lang="ts">
import { computed } from "vue";

import Textarea from "primevue/textarea";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { payload } = defineProps<{
    payload?: GroupPayload;
}>();

const payloadText = computed<string>(() => {
    if (!payload) {
        return "";
    }

    return JSON.stringify(payload, null, 4);
});
</script>

<template>
    <Textarea
        class="payload-analyzer-textarea"
        :model-value="payloadText"
        rows="38"
        readonly
    />
</template>
