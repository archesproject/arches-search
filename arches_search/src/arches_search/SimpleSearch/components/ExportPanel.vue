<script setup lang="ts">
import { ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import InputText from "primevue/inputtext";

import { exportSearchResults } from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

const { $gettext } = useGettext();
const { searchResults, getExportPayload } = useSearchFilters();

const isExporting = ref(false);
const exportError = ref<string | null>(null);
const filename = ref("search_export");

async function onExport() {
    isExporting.value = true;
    exportError.value = null;

    try {
        const payload = getExportPayload();
        await exportSearchResults({
            ...payload,
            filename: filename.value,
        });
    } catch (error) {
        exportError.value =
            error instanceof Error ? error.message : $gettext("Export failed");
    } finally {
        isExporting.value = false;
    }
}
</script>

<template>
    <div class="export-panel">
        <div class="panel-tabs">
            <button class="panel-tab active">
                {{ $gettext("Export Results") }}
            </button>
        </div>

        <div class="panel-controls">
            <label
                for="export-filename"
                class="form-label"
            >
                {{ $gettext("File name") }}
            </label>
            <InputText
                id="export-filename"
                v-model="filename"
                class="filter-input"
                fluid
            />
        </div>

        <div class="panel-list">
            <div class="export-item">
                <div class="item-header">
                    <i class="pi pi-file-excel item-icon" />
                    <span class="item-name">
                        {{ $gettext("Excel Export") }}
                    </span>
                </div>
                <div class="item-meta">
                    <span class="item-type">
                        {{
                            $gettext("%{count} results", {
                                count: String(
                                    searchResults.pagination.total_results,
                                ),
                            })
                        }}
                    </span>
                </div>
                <p class="item-description">
                    {{
                        $gettext(
                            "Export resource descriptors, graph slug, and resource instance ID to an Excel file.",
                        )
                    }}
                </p>

                <div
                    v-if="exportError"
                    class="export-error"
                >
                    <i class="pi pi-exclamation-triangle" />
                    {{ exportError }}
                </div>

                <div class="item-actions">
                    <Button
                        :label="
                            isExporting
                                ? $gettext('Exporting...')
                                : $gettext('Export to Excel')
                        "
                        icon="pi pi-download"
                        icon-pos="left"
                        size="small"
                        text
                        :loading="isExporting"
                        :disabled="
                            isExporting ||
                            searchResults.pagination.total_results === 0
                        "
                        class="action-btn"
                        @click="onExport"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.export-panel {
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

.panel-controls {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0.8rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.form-label {
    font-weight: 500;
    font-size: var(--p-arches-search-font-size);
}

:deep(.filter-input .p-inputtext),
:deep(.filter-input) {
    font-size: var(--p-arches-search-font-size);
}

.panel-list {
    flex: 1;
    overflow-y: auto;
}

.export-item {
    padding: 0.8rem;
    border-bottom: 0.0625rem solid var(--p-content-border-color);
}

.export-item:hover {
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

.export-error {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--p-red-500);
    margin-bottom: 0.4rem;
}

.item-actions {
    display: flex;
    gap: 0.4rem;
}

.action-btn {
    font-size: var(--p-arches-search-font-size);
    padding: 0.2rem 0.4rem;
}
</style>
