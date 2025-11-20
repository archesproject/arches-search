<script setup lang="ts">
import { ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Textarea from "primevue/textarea";

import { getSearchSQL } from "@/arches_search/AdvancedSearch/api.ts";

import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { payload } = defineProps<{
    payload?: GroupPayload;
}>();

const sqlTextValue = ref<string>("");
const isLoadingSQL = ref<boolean>(false);
const sqlErrorMessage = ref<string | null>(null);

watch(
    () => payload,
    () => {
        void fetchSearchSQL();
    },
    { immediate: true },
);

async function fetchSearchSQL(): Promise<void> {
    if (!payload) {
        sqlTextValue.value = "";
        sqlErrorMessage.value = null;
        return;
    }

    isLoadingSQL.value = true;
    sqlErrorMessage.value = null;

    try {
        const responseData = await getSearchSQL(
            payload as unknown as { [key: string]: unknown },
        );

        sqlTextValue.value = responseData.sql;
    } catch (error) {
        if (error instanceof Error) {
            sqlErrorMessage.value = error.message;
        } else {
            sqlErrorMessage.value = $gettext(
                "An unknown error occurred while fetching SQL.",
            );
        }
        sqlTextValue.value = "";
    } finally {
        isLoadingSQL.value = false;
    }
}
</script>

<template>
    <Textarea
        v-model="sqlTextValue"
        class="payload-analyzer-textarea"
        :auto-resize="false"
        rows="38"
    />
</template>
