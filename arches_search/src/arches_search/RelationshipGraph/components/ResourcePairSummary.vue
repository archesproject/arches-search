<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Skeleton from "openvue/skeleton";

import {
    FAILED,
    LOADED,
    LOADING,
} from "@/arches_search/RelationshipGraph/composables/useRelationshipSummaries.ts";

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

function relationshipTypeLabel(label: string): string {
    return label || $gettext("Unspecified relationship");
}
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

        <div
            v-else-if="hasFailed"
            class="message"
        >
            <span>{{
                $gettext("How they are related could not be loaded.")
            }}</span>
            <Button
                variant="link"
                :label="$gettext('Try again')"
                @click="emit('retry')"
            />
        </div>

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
                    <span class="resource">{{ fromTitle }}</span>
                    {{ " " }}
                    <span class="relationship-type">
                        {{
                            relationshipTypeLabel(
                                relationship.relationship_type_label,
                            )
                        }}
                    </span>
                    {{ " " }}
                    <span class="resource">{{ toTitle }}</span>
                </li>
            </ul>
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
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
}

.resource-pair-summary .hops-row .hops {
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--p-text-color);
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
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.6rem;
    font-size: 1.3rem;
    color: var(--p-text-color);
}

.resource-pair-summary .relationships .relationship .resource {
    font-weight: 600;
    overflow-wrap: anywhere;
}

.resource-pair-summary .relationships .relationship .relationship-type {
    padding: 0.1rem 0.8rem;
    border-radius: var(--arches-search-radius-pill);
    background: var(--arches-search-chip-search-bg);
    color: var(--arches-search-chip-search-text);
    font-size: 1.2rem;
}

.resource-pair-summary .loading .loading-row {
    block-size: 3.6rem;
}

.resource-pair-summary .message {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 1.3rem;
    color: var(--p-text-muted-color);
}
</style>
