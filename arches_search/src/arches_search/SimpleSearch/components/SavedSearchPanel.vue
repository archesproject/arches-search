<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
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

const { $gettext } = useGettext();
const toast = useToast();
const { getSearchDefinition } = useSearchFilters();

const emit = defineEmits<{
    (event: "run-query", queryDefinition: Record<string, unknown>): void;
    (event: "open-export"): void;
    (event: "close"): void;
}>();

const activeTab = ref<"save" | "mine" | "shared">("save");
const filterText = ref("");
const sortValue = ref("aToZ");
const searches = ref<SavedSearch[]>([]);
const isLoading = ref(false);

const saveSearchName = ref("");
const saveSearchDescription = ref("");
const isSaving = ref(false);

async function onSaveSearch(): Promise<void> {
    const name = saveSearchName.value.trim();
    if (!name) return;

    isSaving.value = true;
    try {
        await createSavedSearch(
            name,
            saveSearchDescription.value.trim(),
            getSearchDefinition() as unknown as Record<string, unknown>,
        );
        saveSearchName.value = "";
        saveSearchDescription.value = "";
        toast.add({
            severity: "success",
            life: 3000,
            summary: $gettext("Search saved"),
        });
        if (activeTab.value === "mine") {
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

const sortOptions: SortOption[] = [
    { label: $gettext("Sort A to Z"), value: "aToZ" },
    { label: $gettext("Sort Z to A"), value: "zToA" },
    { label: $gettext("Newest first"), value: "newest" },
    { label: $gettext("Oldest first"), value: "oldest" },
];

async function loadSearches() {
    if (activeTab.value === "save") return;

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
</script>

<template>
    <div class="saved-search-panel">
        <div class="panel-header">
            <span class="panel-header-title">
                <i class="pi pi-bookmark-fill" />
                {{ $gettext("Save/Export Search") }}
            </span>
            <button
                class="panel-close-btn"
                @click="emit('close')"
            >
                <i class="pi pi-times" />
                {{ $gettext("Close") }}
            </button>
        </div>

        <div class="panel-tabs">
            <button
                :class="['panel-tab', { active: activeTab === 'save' }]"
                @click="activeTab = 'save'"
            >
                {{ $gettext("Save/Export this search") }}
            </button>
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

        <div
            v-if="activeTab === 'save'"
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
                    fluid
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
                    fluid
                    rows="3"
                />
            </div>
            <div class="save-form-actions">
                <Button
                    :label="$gettext('Save')"
                    icon="pi pi-check"
                    :loading="isSaving"
                    :disabled="isSaving || !saveSearchName.trim()"
                    @click="onSaveSearch"
                />
                <Button
                    :label="$gettext('Export')"
                    icon="pi pi-upload"
                    severity="secondary"
                    class="export-trigger-btn"
                    @click="emit('open-export')"
                />
            </div>
        </div>

        <template v-else>
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
                            :class="[
                                isDynamicQuery(search)
                                    ? 'pi pi-bolt'
                                    : 'pi pi-database',
                                isDynamicQuery(search)
                                    ? 'chip-live'
                                    : 'chip-snapshot',
                            ]"
                            class="item-icon query-type-chip"
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
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.8rem;
    font-family: inherit;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--p-text-muted-color);
    background: none;
    border: none;
    border-radius: 0.4rem;
    cursor: pointer;
    transition: background 0.12s;
}

.panel-close-btn:hover {
    background: var(--p-content-hover-background);
    color: var(--p-text-color);
}

.panel-tabs {
    display: flex;
    flex-shrink: 0;
    padding: 0.3125rem 0.75rem;
    border-bottom: 0.0625rem solid var(--p-content-border-color);
}

.panel-tab {
    flex: 1;
    padding: 0.5rem 0.625rem;
    background: none;
    border: none;
    border-bottom: 0.125rem solid transparent;
    cursor: pointer;
    font-size: var(--p-arches-search-font-size);
    font-family: inherit;
    font-weight: 500;
    text-align: center;
    white-space: nowrap;
    color: var(--p-text-muted-color);
    transition:
        background-color 0.12s,
        color 0.12s,
        border-color 0.12s;
}

.panel-tab.active {
    border-bottom-color: var(--p-primary-color);
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
    letter-spacing: 0.04em;
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
    border-bottom: 0.125rem solid var(--p-content-border-color);
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
    width: 13rem;
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
    box-shadow: 0 0.1rem 0.3rem rgba(0, 0, 0, 0.08);
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

.item-icon.query-type-chip {
    font-size: 1rem;
    padding: 0.25rem;
    border-radius: 999rem;
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
    font-size: 0.85em;
    color: var(--p-text-muted-color);
    margin-bottom: 0.2rem;
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
    margin-top: 0.125rem;
}

.action-btn {
    font-size: 0.85em;
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
