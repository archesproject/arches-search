<script setup lang="ts">
import { computed, ref, watch, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import InputText from "openvue/inputtext";
import Select from "openvue/select";

import { useToast } from "openvue/usetoast";
import {
    getSavedSearches,
    deleteSavedSearch,
    deleteResourceSet,
    getSavedResourceSets,
} from "@/arches_search/SimpleSearch/api.ts";

import type {
    SavedResourceSet,
    SavedSearch,
    SortOption,
} from "@/arches_search/SimpleSearch/types.ts";

const MINE_SCOPE = "mine" as const;

const SORT_A_TO_Z = "aToZ" as const;
const SORT_Z_TO_A = "zToA" as const;
const SORT_NEWEST = "newest" as const;
const SORT_OLDEST = "oldest" as const;

const RUN_QUERY_EVENT = "run-query" as const;

type SavedSearchSortValue =
    | typeof SORT_A_TO_Z
    | typeof SORT_Z_TO_A
    | typeof SORT_NEWEST
    | typeof SORT_OLDEST;

// "mine" lists the user's own searches and resource sets, which they can
// delete; "shared" lists searches others shared with them.
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

const filterText = ref("");
const sortValue = ref<SavedSearchSortValue>(SORT_A_TO_Z);
const searches = ref<SavedSearch[]>([]);
const resourceSets = ref<SavedResourceSet[]>([]);
const isLoading = ref(false);

const sortOptions: SortOption[] = [
    { label: $gettext("Sort A to Z"), value: SORT_A_TO_Z },
    { label: $gettext("Sort Z to A"), value: SORT_Z_TO_A },
    { label: $gettext("Newest first"), value: SORT_NEWEST },
    { label: $gettext("Oldest first"), value: SORT_OLDEST },
];

// The user's own resource sets, listed under "mine" and filtered here by the
// filter text.
const listedResourceSets = computed<SavedResourceSet[]>(() => {
    if (scope !== MINE_SCOPE) {
        return [];
    }
    const filter = filterText.value.trim().toLowerCase();
    return resourceSets.value.filter(
        (resourceSet) =>
            !filter ||
            resourceSet.name.toLowerCase().includes(filter) ||
            (resourceSet.description ?? "").toLowerCase().includes(filter),
    );
});

// Saved searches and resource sets, sorted together.
const listedItems = computed<
    (SavedSearch | (SavedResourceSet & { created_at: string }))[]
>(() =>
    sortSearches([
        ...searches.value,
        ...listedResourceSets.value.map((resourceSet) => ({
            ...resourceSet,
            created_at: resourceSet.date_created,
        })),
    ]),
);

watchEffect(async () => {
    await loadSearches();
});

watch(sortValue, () => {
    searches.value = sortSearches(searches.value);
});

watch(
    () => scope,
    async (value) => {
        if (value === MINE_SCOPE) {
            await loadResourceSets();
        }
    },
    { immediate: true },
);

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

async function loadResourceSets(): Promise<void> {
    try {
        resourceSets.value = (await getSavedResourceSets()).resource_sets;
    } catch {
        // e.g. not signed in.
        resourceSets.value = [];
    }
}

function sortSearches<T extends Pick<SavedSearch, "name" | "created_at">>(
    items: T[],
): T[] {
    const sorted = [...items];
    // Unnamed items (e.g. sets made in arches-resource-sets) go last either way.
    const byName = (left: T, right: T, direction: 1 | -1): number => {
        if (!left.name || !right.name) {
            return Number(!left.name) - Number(!right.name);
        }
        return direction * left.name.localeCompare(right.name);
    };
    switch (sortValue.value) {
        case SORT_Z_TO_A:
            sorted.sort((left, right) => byName(left, right, -1));
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
            sorted.sort((left, right) => byName(left, right, 1));
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

async function onDeleteResourceSet(
    resourceSetToDelete: SavedResourceSet,
): Promise<void> {
    try {
        await deleteResourceSet(resourceSetToDelete.id);
        resourceSets.value = resourceSets.value.filter(
            (resourceSet) => resourceSet.id !== resourceSetToDelete.id,
        );
    } catch (error) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("Failed to delete resource set"),
            detail: (error as Error).message,
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
    <div class="saved-search-list">
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
                v-else-if="listedItems.length === 0"
                class="panel-empty"
            >
                {{ $gettext("No saved searches found") }}
            </div>
            <template
                v-for="item in listedItems"
                v-else
                :key="'savedsearchid' in item ? item.savedsearchid : item.id"
            >
                <div
                    v-if="'savedsearchid' in item"
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
                            v-if="isDynamicQuery(item)"
                            icon="pi pi-play"
                            icon-pos="left"
                            size="small"
                            class="action-btn"
                            :label="$gettext('Run query')"
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
                            v-if="scope === MINE_SCOPE"
                            icon="pi pi-times"
                            icon-pos="left"
                            size="small"
                            class="action-btn action-delete"
                            :label="$gettext('Delete')"
                            :text="true"
                            @click="onDelete(item)"
                        />
                    </div>
                </div>
                <div
                    v-else
                    class="saved-search-item"
                >
                    <div class="item-header">
                        <i
                            class="item-icon query-type-chip pi pi-database chip-snapshot"
                        />
                        <span
                            class="item-name"
                            :class="{ 'item-untitled': !item.name }"
                        >
                            {{ item.name || $gettext("Untitled set") }}
                        </span>
                    </div>
                    <div class="item-meta">
                        <span class="item-type">
                            {{
                                $gettext("Static set · %{count} resources", {
                                    count: String(item.member_count),
                                })
                            }}
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
                            icon="pi pi-times"
                            icon-pos="left"
                            size="small"
                            class="action-btn action-delete"
                            :label="$gettext('Delete')"
                            :text="true"
                            @click="onDeleteResourceSet(item)"
                        />
                    </div>
                </div>
            </template>
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

.item-untitled {
    font-style: italic;
    font-weight: 400;
    color: var(--p-text-muted-color);
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
