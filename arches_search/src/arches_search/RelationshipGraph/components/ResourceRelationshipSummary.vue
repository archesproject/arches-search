<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Skeleton from "openvue/skeleton";

import LoadFailedMessage from "@/arches_search/RelationshipGraph/components/LoadFailedMessage.vue";
import RelationshipSummaryRow from "@/arches_search/RelationshipGraph/components/RelationshipSummaryRow.vue";
import { useGraphColors } from "@/arches_search/RelationshipGraph/composables/useGraphColors.ts";
import {
    FAILED,
    LOADED,
    LOADING,
} from "@/arches_search/RelationshipGraph/utils/load-status.ts";

import type { SummaryState } from "@/arches_search/RelationshipGraph/composables/useRelationshipSummaries.ts";

const LOADING_PLACEHOLDER_COUNT = 3;

const { title, summaryState, deselectedRowIds } = defineProps<{
    title: string;
    summaryState: SummaryState | undefined;
    deselectedRowIds: string[];
}>();

const emit = defineEmits<{
    (event: "toggle-row", rowId: string): void;
    (event: "retry"): void;
    (event: "remove"): void;
}>();

const { $gettext } = useGettext();
const { colorFor } = useGraphColors();

const resourceModel = computed(() =>
    summaryState?.status === LOADED
        ? summaryState.summary.resource_model
        : null,
);

const rows = computed(() =>
    summaryState?.status === LOADED ? summaryState.summary.rows : [],
);

const isLoading = computed<boolean>(
    () => summaryState === undefined || summaryState.status === LOADING,
);

const hasFailed = computed<boolean>(() => summaryState?.status === FAILED);

const removeLabel = computed<string>(() =>
    $gettext("Remove %{title} from the panel", { title }),
);
</script>

<template>
    <section class="resource-relationship-summary">
        <header class="header">
            <span
                v-if="resourceModel"
                class="swatch"
                :style="{ backgroundColor: colorFor(resourceModel) }"
            />
            <div class="heading">
                <h4 class="title">{{ title }}</h4>
                <span
                    v-if="resourceModel"
                    class="model-name"
                >
                    {{ resourceModel.name }}
                </span>
            </div>
            <Button
                class="remove"
                variant="text"
                size="small"
                icon="pi pi-times"
                :aria-label="removeLabel"
                :title="removeLabel"
                @click="emit('remove')"
            />
        </header>

        <div
            v-if="isLoading"
            class="loading"
        >
            <Skeleton
                v-for="placeholder in LOADING_PLACEHOLDER_COUNT"
                :key="placeholder"
                class="loading-row"
            />
        </div>

        <LoadFailedMessage
            v-else-if="hasFailed"
            :message="$gettext('The relationships could not be loaded.')"
            @retry="emit('retry')"
        />

        <div
            v-else-if="rows.length === 0"
            class="message"
        >
            <span>{{ $gettext("This resource has no relationships.") }}</span>
        </div>

        <ul
            v-else
            class="rows"
        >
            <RelationshipSummaryRow
                v-for="row in rows"
                :key="row.id"
                :row="row"
                :selected="!deselectedRowIds.includes(row.id)"
                @toggle="emit('toggle-row', row.id)"
            />
        </ul>
    </section>
</template>

<style scoped>
.resource-relationship-summary {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}

.resource-relationship-summary .header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding-block-end: 0.6rem;
    border-block-end: 0.125rem solid var(--p-content-border-color);
}

.resource-relationship-summary .header .swatch {
    flex-shrink: 0;
    inline-size: 1.8rem;
    block-size: 1.8rem;
    border-radius: 50%;
}

.resource-relationship-summary .header .heading {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-inline-size: 0;
}

.resource-relationship-summary .header .heading .title {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--p-text-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.resource-relationship-summary .header .heading .model-name {
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
}

.resource-relationship-summary .header .remove {
    flex-shrink: 0;
}

.resource-relationship-summary .rows {
    margin: 0;
    padding: 0;
    list-style: none;
}

.resource-relationship-summary .loading {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    padding-block: 0.8rem;
}

.resource-relationship-summary .loading .loading-row {
    block-size: 3.6rem;
}

.resource-relationship-summary .message {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding-block: 1rem;
    font-size: 1.3rem;
    color: var(--p-text-muted-color);
}
</style>
