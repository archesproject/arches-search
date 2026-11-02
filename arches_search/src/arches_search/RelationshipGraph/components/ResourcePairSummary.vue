<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Skeleton from "openvue/skeleton";

import LoadFailedMessage from "@/arches_search/RelationshipGraph/components/LoadFailedMessage.vue";
import RelationshipSentence from "@/arches_search/RelationshipGraph/components/RelationshipSentence.vue";

import {
    FAILED,
    LOADED,
    LOADING,
} from "@/arches_search/RelationshipGraph/utils/load-status.ts";

import type { PathState } from "@/arches_search/RelationshipGraph/composables/useResourcePath.ts";

const { fromTitle, toTitle, pathState, isPathShown } = defineProps<{
    fromTitle: string;
    toTitle: string;
    pathState: PathState | null;
    isPathShown: boolean;
}>();

const emit = defineEmits<{
    (event: "toggle-path"): void;
    (event: "retry"): void;
}>();

const { $gettext, $ngettext } = useGettext();

const path = computed(() =>
    pathState?.status === LOADED ? pathState.path : null,
);

const isLoading = computed<boolean>(
    () => pathState === null || pathState.status === LOADING,
);

const hasFailed = computed<boolean>(() => pathState?.status === FAILED);

const hopsMessage = computed<string>(() => {
    if (!path.value) return "";
    if (path.value.hops !== null) {
        return $ngettext(
            "%{count} hop apart",
            "%{count} hops apart",
            path.value.hops,
            { count: String(path.value.hops) },
        );
    }
    if (path.value.limit_reached) {
        return $gettext(
            "The search stopped before it could tell whether they are connected.",
        );
    }
    return $ngettext(
        "Not connected within %{count} hop.",
        "Not connected within %{count} hops.",
        path.value.max_hops,
        { count: String(path.value.max_hops) },
    );
});

const togglePathLabel = computed<string>(() =>
    isPathShown
        ? $gettext("Hide the path from the graph")
        : $gettext("Show the path in the graph"),
);
</script>

<template>
    <section class="resource-pair-summary">
        <header class="header">
            <i class="pi pi-arrows-h" />
            <h4 class="title">{{ $gettext("Between these resources") }}</h4>
        </header>

        <div
            v-if="isLoading"
            class="loading"
        >
            <Skeleton class="loading-row" />
        </div>

        <LoadFailedMessage
            v-else-if="hasFailed"
            :message="$gettext('How they are related could not be loaded.')"
            @retry="emit('retry')"
        />

        <template v-else-if="path">
            <div class="hops-row">
                <span class="hops">{{ hopsMessage }}</span>
                <Button
                    v-if="path.hops !== null"
                    class="path-toggle"
                    variant="text"
                    size="small"
                    :icon="isPathShown ? 'pi pi-eye' : 'pi pi-eye-slash'"
                    :label="togglePathLabel"
                    :aria-pressed="isPathShown"
                    @click="emit('toggle-path')"
                />
            </div>

            <ul
                v-if="path.direct_relationships.length > 0"
                class="relationships"
            >
                <li
                    v-for="relationship in path.direct_relationships"
                    :key="relationship.id"
                    class="relationship"
                >
                    <RelationshipSentence
                        :from-name="fromTitle"
                        :to-name="toTitle"
                        :label="relationship.relationship_type_label"
                    />
                </li>
            </ul>
            <p
                v-if="path.direct_relationships_truncated"
                role="status"
            >
                {{
                    $gettext(
                        "Some direct relationships are not shown because the relationship limit was reached.",
                    )
                }}
            </p>
        </template>
    </section>
</template>

<style scoped>
.resource-pair-summary {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.resource-pair-summary .header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding-block-end: 0.6rem;
    border-block-end: 0.125rem solid var(--p-content-border-color);
    color: var(--p-primary-color);
}

.resource-pair-summary .header .title {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--p-text-color);
}

.resource-pair-summary .hops-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 0.4rem 1rem;
}

.resource-pair-summary .hops-row .hops {
    white-space: nowrap;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--p-text-color);
}

/* One and a half times a small text button */
.resource-pair-summary .hops-row .path-toggle.p-button {
    flex-shrink: 0;
    font-size: 1.3rem;
}

/* The icon takes its size from the theme, not from the button */
.resource-pair-summary .hops-row .path-toggle.p-button :deep(.p-button-icon) {
    font-size: 1.3rem;
}

.resource-pair-summary .relationships {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin: 0;
    padding: 0;
    list-style: none;
}

.resource-pair-summary .relationships .relationship {
    font-size: 1.3rem;
    color: var(--p-text-color);
}

.resource-pair-summary .loading .loading-row {
    block-size: 3.6rem;
}
</style>
