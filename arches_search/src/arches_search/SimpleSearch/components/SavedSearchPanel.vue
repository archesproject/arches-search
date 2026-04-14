<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Select from "primevue/select";

import {
    getSavedSearches,
    deleteSavedSearch,
} from "@/arches_search/SimpleSearch/api.ts";

import type {
    SavedSearch,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";

const { $gettext } = useGettext();

const emit = defineEmits<{
    (event: "run-query", queryDefinition: Record<string, unknown>): void;
}>();

const activeTab = ref<"mine" | "shared">("mine");
const filterText = ref("");
const sortValue = ref("aToZ");
const searches = ref<SavedSearch[]>([]);
const isLoading = ref(false);

const sortOptions: SortOption[] = [
    { label: $gettext("Sort A to Z"), value: "aToZ" },
    { label: $gettext("Sort Z to A"), value: "zToA" },
    { label: $gettext("Newest first"), value: "newest" },
    { label: $gettext("Oldest first"), value: "oldest" },
];

async function loadSearches() {
    isLoading.value = true;
    try {
        const results = await getSavedSearches(
            activeTab.value,
            filterText.value,
        );
        searches.value = sortSearches(results);
    } catch {
        searches.value = [];
    } finally {
        isLoading.value = false;
    }
}

function sortSearches(items: SavedSearch[]): SavedSearch[] {
    const sorted = [...items];
    switch (sortValue.value) {
        case "zToA":
            sorted.sort((a, b) => b.name.localeCompare(a.name));
            break;
        case "newest":
            sorted.sort(
                (a, b) =>
                    new Date(b.created_at).getTime() -
                    new Date(a.created_at).getTime(),
            );
            break;
        case "oldest":
            sorted.sort(
                (a, b) =>
                    new Date(a.created_at).getTime() -
                    new Date(b.created_at).getTime(),
            );
            break;
        default:
            sorted.sort((a, b) => a.name.localeCompare(b.name));
    }
    return sorted;
}

async function onDelete(search: SavedSearch) {
    try {
        await deleteSavedSearch(search.savedsearchid);
        searches.value = searches.value.filter(
            (s) => s.savedsearchid !== search.savedsearchid,
        );
    } catch {
        // handled silently for now
    }
}

function formatDate(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleString();
}

function isDynamicQuery(search: SavedSearch): boolean {
    const qd = search.query_definition;
    return qd != null && ("groups" in qd || "terms" in qd);
}

watch([activeTab, filterText], () => loadSearches());
watch(sortValue, () => {
    searches.value = sortSearches(searches.value);
});

onMounted(() => loadSearches());

defineExpose({ loadSearches });
</script>

<template>
    <div class="saved-search-panel">
        <div class="panel-tabs">
            <button
                :class="['panel-tab', { active: activeTab === 'mine' }]"
                @click="activeTab = 'mine'"
            >
                {{ $gettext("My Saved Searches") }}
            </button>
            <button
                :class="['panel-tab', { active: activeTab === 'shared' }]"
                @click="activeTab = 'shared'"
            >
                {{ $gettext("Shared Searches") }}
            </button>
        </div>

        <div class="panel-controls">
            <InputText
                v-model="filterText"
                :placeholder="$gettext('Find...')"
                class="filter-input"
                fluid
            />
            <div class="sort-row">
                <Select
                    v-model="sortValue"
                    :options="sortOptions"
                    option-label="label"
                    option-value="value"
                    class="sort-select"
                    variant="filled"
                />
            </div>
        </div>

        <div class="panel-list">
            <div
                v-if="isLoading"
                class="panel-empty"
            >
                {{ $gettext("Loading...") }}
            </div>
            <div
                v-else-if="searches.length === 0"
                class="panel-empty"
            >
                {{ $gettext("No saved searches found") }}
            </div>
            <div
                v-for="search in searches"
                v-else
                :key="search.savedsearchid"
                class="saved-search-item"
            >
                <div class="item-header">
                    <i
                        :class="
                            isDynamicQuery(search)
                                ? 'pi pi-bolt'
                                : 'pi pi-database'
                        "
                        class="item-icon"
                    />
                    <span class="item-name">{{ search.name }}</span>
                </div>
                <div class="item-meta">
                    <span class="item-type">
                        {{
                            isDynamicQuery(search)
                                ? $gettext("Dynamic query")
                                : $gettext("Saved Results")
                        }}
                    </span>
                    <span class="item-date">
                        {{ $gettext("Saved:") }}
                        {{ formatDate(search.created_at) }}
                    </span>
                </div>
                <p
                    v-if="search.description"
                    class="item-description"
                >
                    {{ search.description }}
                </p>
                <p
                    v-else
                    class="item-description item-no-description"
                >
                    {{ $gettext("No description provided") }}
                </p>
                <div class="item-actions">
                    <Button
                        v-if="isDynamicQuery(search)"
                        :label="$gettext('Run query')"
                        icon="pi pi-play"
                        icon-pos="left"
                        size="small"
                        text
                        class="action-btn"
                        @click="emit('run-query', search.query_definition)"
                    />
                    <Button
                        v-else
                        :label="$gettext('Show results')"
                        icon="pi pi-play"
                        icon-pos="left"
                        size="small"
                        text
                        disabled
                        class="action-btn"
                    />
                    <Button
                        v-if="activeTab === 'mine'"
                        :label="$gettext('Delete')"
                        icon="pi pi-times"
                        icon-pos="left"
                        size="small"
                        text
                        class="action-btn action-delete"
                        @click="onDelete(search)"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.saved-search-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    font-size: var(--p-arches-search-font-size);
}

.panel-tabs {
    display: flex;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.panel-tab {
    flex: 1;
    padding: 0.8rem;
    background: none;
    border: none;
    border-bottom: 0.2rem solid transparent;
    cursor: pointer;
    font-size: var(--p-arches-search-font-size);
    font-family: inherit;
    font-weight: 500;
    text-align: center;
}

.panel-tab.active {
    border-bottom-color: var(--p-primary-color);
    font-weight: 600;
}

.panel-tab:hover:not(.active) {
    background-color: var(--p-surface-100);
}

.panel-controls {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0.8rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

:deep(.filter-input .p-inputtext),
:deep(.filter-input) {
    font-size: var(--p-arches-search-font-size);
}

.sort-row {
    display: flex;
    justify-content: flex-end;
}

:deep(.sort-select .p-select-label) {
    font-size: var(--p-arches-search-font-size);
}

:deep(.sort-select) {
    border: none;
    box-shadow: none;
    background: transparent;
}

.panel-list {
    flex: 1;
    overflow-y: auto;
}

.panel-empty {
    padding: 1.6rem;
    text-align: center;
    color: var(--p-surface-400);
}

.saved-search-item {
    padding: 0.8rem;
    border-bottom: 0.0625rem solid var(--p-content-border-color);
}

.saved-search-item:hover {
    background-color: var(--p-surface-50);
}

.item-header {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-bottom: 0.2rem;
}

.item-icon {
    color: var(--p-primary-color);
}

.item-name {
    font-weight: 600;
    color: var(--p-primary-color);
}

.item-meta {
    display: flex;
    gap: 0.6rem;
    font-size: 0.85em;
    color: var(--p-surface-500);
    margin-bottom: 0.2rem;
}

.item-description {
    margin: 0.2rem 0 0.4rem;
    color: var(--p-surface-700);
}

.item-no-description {
    font-style: italic;
    color: var(--p-surface-400);
}

.item-actions {
    display: flex;
    gap: 0.4rem;
}

.action-btn {
    font-size: var(--p-arches-search-font-size);
    padding: 0.2rem 0.4rem;
}

.action-delete {
    color: var(--p-red-500);
}
</style>
