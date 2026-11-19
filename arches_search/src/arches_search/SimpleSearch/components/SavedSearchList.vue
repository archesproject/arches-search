<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import ConfirmDialog from "openvue/confirmdialog";
import InputText from "openvue/inputtext";
import Select from "openvue/select";

import { useConfirm } from "openvue/useconfirm";
import { useToast } from "openvue/usetoast";
import {
    getSavedSearches,
    deleteSavedSearch,
} from "@/arches_search/SimpleSearch/api.ts";

import type {
    SavedSearch,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";

const MINE_SCOPE = "mine" as const;

const SORT_A_TO_Z = "aToZ" as const;
const SORT_Z_TO_A = "zToA" as const;
const SORT_NEWEST = "newest" as const;
const SORT_OLDEST = "oldest" as const;

const RUN_QUERY_EVENT = "run-query" as const;

// Keeps this list's dialog apart from any other ConfirmDialog on the page.
const CONFIRM_GROUP = "saved-search-list" as const;

type SavedSearchSortValue =
    | typeof SORT_A_TO_Z
    | typeof SORT_Z_TO_A
    | typeof SORT_NEWEST
    | typeof SORT_OLDEST;

// "mine" lists the user's own searches, which they can delete; "shared" lists
// searches others shared with them.
const { scope } = defineProps<{
    scope: "mine" | "shared";
}>();

const emit = defineEmits<{
    (
        event: typeof RUN_QUERY_EVENT,
        queryDefinition: Record<string, unknown>,
        searchName: string,
    ): void;
}>();

const { $gettext } = useGettext();
const toast = useToast();
const confirm = useConfirm();

const filterText = ref("");
const sortValue = ref<SavedSearchSortValue>(SORT_A_TO_Z);
const searches = ref<SavedSearch[]>([]);
const isLoading = ref(false);

const sortOptions: SortOption[] = [
    { label: $gettext("Sort A to Z"), value: SORT_A_TO_Z },
    { label: $gettext("Sort Z to A"), value: SORT_Z_TO_A },
    { label: $gettext("Newest first"), value: SORT_NEWEST },
    { label: $gettext("Oldest first"), value: SORT_OLDEST },
];

watchEffect(async () => {
    await loadSearches();
});

watch(sortValue, () => {
    searches.value = sortSearches(searches.value);
});

async function loadSearches(): Promise<void> {
    isLoading.value = true;
    try {
        const results = await getSavedSearches(scope, filterText.value);
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
        case SORT_Z_TO_A:
            sorted.sort((left, right) => right.name.localeCompare(left.name));
            break;
        case SORT_NEWEST:
            sorted.sort(
                (left, right) =>
                    new Date(right.created_at).getTime() -
                    new Date(left.created_at).getTime(),
            );
            break;
        case SORT_OLDEST:
            sorted.sort(
                (left, right) =>
                    new Date(left.created_at).getTime() -
                    new Date(right.created_at).getTime(),
            );
            break;
        default:
            sorted.sort((left, right) => left.name.localeCompare(right.name));
    }
    return sorted;
}

async function onDelete(search: SavedSearch): Promise<void> {
    try {
        await deleteSavedSearch(search.savedsearchid);
        searches.value = searches.value.filter(
            (savedSearch) => savedSearch.savedsearchid !== search.savedsearchid,
        );
    } catch (error) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("Failed to delete search"),
            detail: (error as Error).message,
        });
    }
}

function confirmDelete(search: SavedSearch): void {
    confirm.require({
        group: CONFIRM_GROUP,
        header: isStaticSet(search)
            ? $gettext("Delete static set")
            : $gettext("Delete saved search"),
        message: $gettext('Delete "%{name}"? This cannot be undone.', {
            name: search.name,
        }),
        icon: "pi pi-exclamation-triangle",
        acceptLabel: $gettext("Delete"),
        rejectLabel: $gettext("Cancel"),
        acceptProps: { severity: "danger" },
        rejectProps: { severity: "secondary", outlined: true },
        accept: () => onDelete(search),
    });
}

function formatDate(isoDateString: string): string {
    const date = new Date(isoDateString);
    return date.toLocaleString();
}

function isStaticSet(search: SavedSearch): boolean {
    return typeof search.query_definition?.resourceSetId === "string";
}

function queryTypeIconClasses(search: SavedSearch): string[] {
    if (isStaticSet(search)) {
        return ["pi", "pi-database", "chip-snapshot"];
    }
    return ["pi", "pi-bolt", "chip-live"];
}

function queryTypeLabel(search: SavedSearch): string {
    if (isStaticSet(search)) {
        return $gettext("Static set");
    }
    return $gettext("Dynamic query");
}
</script>

<template>
    <div class="saved-search-list">
        <ConfirmDialog :group="CONFIRM_GROUP" />
        <div class="panel-controls">
            <InputText
                v-model="filterText"
                class="filter-input"
                :placeholder="$gettext('Find...')"
                :fluid="true"
            />
            <div class="sort-row">
                <Select
                    v-model="sortValue"
                    option-label="label"
                    option-value="value"
                    class="sort-select"
                    variant="filled"
                    :options="sortOptions"
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
                v-for="item in searches"
                v-else
                :key="item.savedsearchid"
                class="saved-search-item"
            >
                <div class="item-header">
                    <i
                        class="item-icon query-type-chip"
                        :class="queryTypeIconClasses(item)"
                    />
                    <span class="item-name">{{ item.name }}</span>
                </div>
                <div class="item-meta">
                    <span class="item-type">
                        {{ queryTypeLabel(item) }}
                    </span>
                    <span class="item-date">
                        {{ $gettext("Saved:") }}
                        {{ formatDate(item.created_at) }}
                    </span>
                </div>
                <p
                    v-if="item.description"
                    class="item-description"
                >
                    {{ item.description }}
                </p>
                <p
                    v-else
                    class="item-description item-no-description"
                >
                    {{ $gettext("No description provided") }}
                </p>
                <div class="item-actions">
                    <Button
                        icon="pi pi-play"
                        icon-pos="left"
                        size="small"
                        class="action-btn"
                        :label="
                            isStaticSet(item)
                                ? $gettext('Show results')
                                : $gettext('Run query')
                        "
                        :text="true"
                        @click="
                            emit(
                                RUN_QUERY_EVENT,
                                item.query_definition,
                                item.name,
                            )
                        "
                    />
                    <Button
                        v-if="scope === MINE_SCOPE"
                        icon="pi pi-times"
                        icon-pos="left"
                        size="small"
                        class="action-btn action-delete"
                        :label="$gettext('Delete')"
                        :text="true"
                        @click="confirmDelete(item)"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.saved-search-list {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
}

.panel-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1rem 0.5rem;
    flex-shrink: 0;
    border-block-end: 0.125rem solid var(--p-content-border-color);
}

.filter-input {
    flex: 1;
    min-width: 0;
}

:deep(.filter-input .p-inputtext),
:deep(.filter-input) {
    font-size: var(--p-arches-search-font-size);
}

.sort-row {
    display: flex;
    justify-content: flex-end;
    flex-shrink: 0;
}

:deep(.sort-select .p-select-label) {
    font-size: var(--p-arches-search-font-size);
}

:deep(.sort-select) {
    flex-shrink: 0;
    border: none;
    box-shadow: none;
    background: transparent;
}

.panel-list {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.panel-empty {
    padding: 1.6rem;
    text-align: center;
    color: var(--p-text-muted-color);
}

.saved-search-item {
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.5rem;
    padding: 0.625rem 0.75rem;
    background: var(--arches-search-page-bg);
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
    transition:
        border-color 0.12s,
        box-shadow 0.12s;
}

.saved-search-item:hover {
    border-color: var(--p-primary-color);
    box-shadow: var(--arches-search-item-hover-shadow);
}

.item-header {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-block-end: 0.2rem;
}

.item-icon {
    color: var(--p-primary-color);
}

.item-icon.query-type-chip {
    font-size: 1rem;
    padding: 0.25rem;
    border-radius: var(--arches-search-radius-pill);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.item-icon.query-type-chip.chip-live {
    background: var(--arches-search-live-bg);
    color: var(--arches-search-live-text);
}

.item-icon.query-type-chip.chip-snapshot {
    background: var(--arches-search-highlight-bg);
    color: var(--arches-search-highlight-text);
}

.item-name {
    font-weight: 600;
    color: var(--p-text-color);
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.item-meta {
    display: flex;
    gap: 0.6rem;
    font-size: 1.36rem;
    color: var(--p-text-muted-color);
    margin-block-end: 0.2rem;
}

.item-description {
    margin: 0.2rem 0 0.4rem;
    color: var(--p-text-muted-color);
}

.item-no-description {
    font-style: italic;
    color: var(--p-text-muted-color);
}

.item-actions {
    display: flex;
    gap: 0.4rem;
    margin-block-start: 0.125rem;
}

.action-btn {
    font-size: 1.36rem;
    padding: 0.3rem 0.9rem;
    background: var(--p-content-background);
    border: 0.1rem solid var(--p-content-border-color);
    border-radius: 0.5rem;
    color: var(--p-text-muted-color);
    transition:
        background-color 0.12s,
        color 0.12s;
}

.action-btn:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.action-delete {
    color: var(--p-red-500);
}
</style>
