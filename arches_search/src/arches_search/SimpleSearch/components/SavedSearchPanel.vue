<script setup lang="ts">
import { ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";
import { useToast } from "primevue/usetoast";

import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Textarea from "primevue/textarea";

import {
    createSavedSearch,
    getSavedSearches,
    deleteSavedSearch,
} from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type {
    SavedSearch,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";

const SAVE_TAB = "save" as const;
const MINE_TAB = "mine" as const;
const SHARED_TAB = "shared" as const;

const SORT_A_TO_Z = "aToZ" as const;
const SORT_Z_TO_A = "zToA" as const;
const SORT_NEWEST = "newest" as const;
const SORT_OLDEST = "oldest" as const;

const RUN_QUERY_EVENT = "run-query" as const;
const OPEN_EXPORT_EVENT = "open-export" as const;
const CLOSE_EVENT = "close" as const;

type SavedSearchSortValue =
    | typeof SORT_A_TO_Z
    | typeof SORT_Z_TO_A
    | typeof SORT_NEWEST
    | typeof SORT_OLDEST;

const { shouldShowHeader = true, shouldShowSaveTab = true } = defineProps<{
    shouldShowHeader?: boolean;
    shouldShowSaveTab?: boolean;
}>();

const emit = defineEmits<{
    (event: "run-query", queryDefinition: Record<string, unknown>): void;
    (event: "open-export"): void;
    (event: "close"): void;
}>();

const { $gettext } = useGettext();
const toast = useToast();
const searchFilters = shouldShowSaveTab ? useSearchFilters() : null;

const activeTab = ref<typeof SAVE_TAB | typeof MINE_TAB | typeof SHARED_TAB>(
    shouldShowSaveTab ? SAVE_TAB : MINE_TAB,
);
const filterText = ref("");
const sortValue = ref<SavedSearchSortValue>(SORT_A_TO_Z);
const searches = ref<SavedSearch[]>([]);
const isLoading = ref(false);

const saveSearchName = ref("");
const saveSearchDescription = ref("");
const isSaving = ref(false);

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

async function onSaveSearch(): Promise<void> {
    const name = saveSearchName.value.trim();
    if (!name || !searchFilters) {
        return;
    }

    isSaving.value = true;
    try {
        await createSavedSearch(
            name,
            saveSearchDescription.value.trim(),
            searchFilters.getSearchDefinition() as unknown as Record<
                string,
                unknown
            >,
        );
        saveSearchName.value = "";
        saveSearchDescription.value = "";
        toast.add({
            severity: "success",
            life: 3000,
            summary: $gettext("Search saved"),
        });
        if (activeTab.value === MINE_TAB) {
            await loadSearches();
        }
    } catch (error) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("Failed to save search"),
            detail: error instanceof Error ? error.message : undefined,
        });
    } finally {
        isSaving.value = false;
    }
}

async function loadSearches(): Promise<void> {
    if (activeTab.value === SAVE_TAB) return;

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
            detail: error instanceof Error ? error.message : undefined,
        });
    }
}

function formatDate(isoDateString: string): string {
    const date = new Date(isoDateString);
    return date.toLocaleString();
}

function isDynamicQuery(search: SavedSearch): boolean {
    const queryDefinition = search.query_definition;
    return (
        queryDefinition != null &&
        ("groups" in queryDefinition || "terms" in queryDefinition)
    );
}

function queryTypeIconClasses(search: SavedSearch): string[] {
    if (isDynamicQuery(search)) {
        return ["pi", "pi-bolt", "chip-live"];
    }
    return ["pi", "pi-database", "chip-snapshot"];
}

function queryTypeLabel(search: SavedSearch): string {
    if (isDynamicQuery(search)) {
        return $gettext("Dynamic query");
    }
    return $gettext("Saved Results");
}
</script>

<template>
    <div class="saved-search-panel">
        <div
            v-if="shouldShowHeader"
            class="panel-header"
        >
            <span class="panel-header-title">
                <i class="pi pi-bookmark-fill" />
                {{ $gettext("Save/Export Search") }}
            </span>
            <Button
                icon="pi pi-times"
                icon-pos="left"
                class="panel-close-btn"
                :label="$gettext('Close')"
                :text="true"
                @click="emit(CLOSE_EVENT)"
            />
        </div>

        <div class="panel-tabs">
            <Button
                v-if="shouldShowSaveTab"
                :label="$gettext('Save/Export this search')"
                :text="true"
                :class="['panel-tab', { active: activeTab === SAVE_TAB }]"
                @click="activeTab = SAVE_TAB"
            />
            <Button
                :label="$gettext('My Saved Searches')"
                :text="true"
                :class="['panel-tab', { active: activeTab === MINE_TAB }]"
                @click="activeTab = MINE_TAB"
            />
            <Button
                :label="$gettext('Shared Searches')"
                :text="true"
                :class="['panel-tab', { active: activeTab === SHARED_TAB }]"
                @click="activeTab = SHARED_TAB"
            />
        </div>

        <div
            v-if="activeTab === SAVE_TAB"
            class="save-form"
        >
            <p class="save-form-hint">
                {{
                    $gettext(
                        "Give this search a name to save it to your account.",
                    )
                }}
            </p>
            <div class="save-form-field">
                <label
                    for="save-search-name"
                    class="save-form-label"
                >
                    {{ $gettext("Search name") }}
                </label>
                <InputText
                    id="save-search-name"
                    v-model="saveSearchName"
                    class="save-form-input"
                    :fluid="true"
                    @keydown.enter="onSaveSearch"
                />
            </div>
            <div class="save-form-field">
                <label
                    for="save-search-description"
                    class="save-form-label"
                >
                    {{ $gettext("Description") }}
                </label>
                <Textarea
                    id="save-search-description"
                    v-model="saveSearchDescription"
                    class="save-form-input"
                    rows="3"
                    :fluid="true"
                />
            </div>
            <div class="save-form-actions">
                <Button
                    icon="pi pi-check"
                    :label="$gettext('Save')"
                    :loading="isSaving"
                    :disabled="isSaving || !saveSearchName.trim()"
                    @click="onSaveSearch"
                />
                <Button
                    icon="pi pi-upload"
                    severity="secondary"
                    class="export-trigger-btn"
                    :label="$gettext('Export')"
                    @click="emit(OPEN_EXPORT_EVENT)"
                />
            </div>
        </div>

        <template v-else>
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
                    v-for="search in searches"
                    v-else
                    :key="search.savedsearchid"
                    class="saved-search-item"
                >
                    <div class="item-header">
                        <i
                            class="item-icon query-type-chip"
                            :class="queryTypeIconClasses(search)"
                        />
                        <span class="item-name">{{ search.name }}</span>
                    </div>
                    <div class="item-meta">
                        <span class="item-type">
                            {{ queryTypeLabel(search) }}
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
                            icon="pi pi-play"
                            icon-pos="left"
                            size="small"
                            class="action-btn"
                            :label="$gettext('Run query')"
                            :text="true"
                            @click="
                                emit(RUN_QUERY_EVENT, search.query_definition)
                            "
                        />
                        <Button
                            v-else
                            icon="pi pi-play"
                            icon-pos="left"
                            size="small"
                            class="action-btn"
                            :label="$gettext('Show results')"
                            :text="true"
                            :disabled="true"
                        />
                        <Button
                            v-if="activeTab === MINE_TAB"
                            icon="pi pi-times"
                            icon-pos="left"
                            size="small"
                            class="action-btn action-delete"
                            :label="$gettext('Delete')"
                            :text="true"
                            @click="onDelete(search)"
                        />
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>

<style scoped>
.saved-search-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    font-size: var(--p-arches-search-font-size);
    background: var(--arches-search-card-bg);
}

.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    padding-inline: 1.6rem;
    min-height: 5.5rem;
    font-weight: 600;
    color: var(--p-text-color);
    background: var(--arches-search-page-bg);
    border-block-end: 0.1rem solid var(--p-content-border-color);
}

.panel-header-title .pi {
    margin-inline-end: 0.6rem;
    color: var(--p-primary-color);
}

.panel-close-btn {
    padding: 0.3rem 0.8rem;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--p-text-muted-color);
    border-radius: 0.4rem;
}

.panel-close-btn:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.panel-tabs {
    display: flex;
    flex-shrink: 0;
    padding: 0.3125rem 0.75rem;
    border-block-end: 0.0625rem solid var(--p-content-border-color);
}

.panel-tab {
    flex: 1;
    min-inline-size: 0;
    padding: 0.5rem 0.625rem;
    overflow: hidden;
    border-block-end: 0.125rem solid transparent;
    border-radius: 0;
    font-size: 1.2rem;
    font-weight: 500;
    white-space: nowrap;
    text-overflow: ellipsis;
    color: var(--p-text-muted-color);
    transition:
        background-color 0.12s,
        color 0.12s,
        border-color 0.12s;
}

.panel-tab.active {
    border-block-end-color: var(--p-primary-color);
    color: var(--p-text-color);
    font-weight: 600;
}

.panel-tab:hover:not(.active) {
    background-color: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.save-form {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 2rem;
    overflow-y: auto;
}

.save-form-hint {
    margin: 0;
    font-size: 1.3rem;
    color: var(--p-text-muted-color);
    line-height: 1.5;
}

.save-form-field {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.save-form-label {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--p-text-muted-color);
    text-transform: uppercase;
    letter-spacing: 0.048rem;
}

:deep(.save-form-input .p-inputtext),
:deep(.save-form-input .p-textarea),
:deep(.save-form-input) {
    font-size: var(--p-arches-search-font-size);
}

.save-form-actions {
    display: flex;
    gap: 0.8rem;
}

.export-trigger-btn.p-button {
    background: var(--p-content-background);
    border-color: var(--p-content-border-color);
    color: var(--p-text-color);
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
