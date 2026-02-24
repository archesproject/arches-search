<script setup lang="ts">
import { ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Textarea from "primevue/textarea";

import { getSearchSQL } from "@/arches_search/AdvancedSearch/api.ts";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { payload } = defineProps<{
    payload: GroupPayload;
}>();

const sqlText = ref("");
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);

watchEffect(() => {
    void fetchSQL(payload);
});

async function fetchSQL(currentPayload: GroupPayload) {
    isLoading.value = true;
    errorMessage.value = null;

    try {
        const response = await getSearchSQL(currentPayload);
        sqlText.value = response.sql;
    } catch (error) {
        if (error instanceof Error) {
            errorMessage.value = error.message;
        } else {
            errorMessage.value = $gettext(
                "An unknown error occurred while fetching SQL.",
            );
        }
        sqlText.value = "";
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
        v-else-if="errorMessage"
        severity="error"
    >
        {{ errorMessage }}
    </Message>

    <Textarea
        v-else
        class="payload-analyzer-textarea"
        :model-value="sqlText"
        rows="38"
        readonly
    />
</template>
