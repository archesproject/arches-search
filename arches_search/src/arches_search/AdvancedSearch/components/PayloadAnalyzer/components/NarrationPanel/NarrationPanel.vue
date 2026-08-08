<script setup lang="ts">
import { ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Textarea from "primevue/textarea";

import { getNarration } from "@/arches_search/AdvancedSearch/api.ts";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { payload } = defineProps<{
    payload: GroupPayload;
}>();

const narration = ref("");
const isLoading = ref(false);
const fetchError = ref<Error | null>(null);

watchEffect(() => {
    void fetchNarration(payload);
});

async function fetchNarration(currentPayload: GroupPayload) {
    isLoading.value = true;
    fetchError.value = null;

    try {
        narration.value = await getNarration(currentPayload);
    } catch (error) {
        fetchError.value =
            error instanceof Error
                ? error
                : new Error(
                      $gettext(
                          "An unknown error occurred while fetching the narration.",
                      ),
                  );
        narration.value = "";
    } finally {
        isLoading.value = false;
    }
}
</script>

<template>
    <Skeleton
        v-if="isLoading"
        class="payload-analyzer-textarea"
    />

    <Message
        v-else-if="fetchError"
        severity="error"
    >
        {{ fetchError.message }}
    </Message>

    <Textarea
        v-else
        class="payload-analyzer-textarea"
        :model-value="narration"
        rows="38"
        readonly
    />
</template>
