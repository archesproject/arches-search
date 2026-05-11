<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import InputText from "primevue/inputtext";
import RadioButton from "primevue/radiobutton";

import { exportSearchResults } from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

const { $gettext } = useGettext();
const { searchResults, getExportPayload } = useSearchFilters();

const isExporting = ref(false);
const exportError = ref<string | null>(null);
const filename = ref("search_export");
const selectedFormat = ref("simple");

const downloadButtonLabel = computed(() =>
    isExporting.value ? $gettext("Downloading...") : $gettext("Download"),
);

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

        <div class="panel-list">
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

            <div class="export-item">
                <div class="item-header">
                    <RadioButton
                        v-model="selectedFormat"
                        input-id="format-simple"
                        value="simple"
                        name="exportFormat"
                    />
                    <label
                        for="format-simple"
                        class="item-name"
                    >
                        {{ $gettext("Simple Export") }}
                    </label>
                </div>
                <p class="item-description">
                    {{
                        $gettext(
                            "Export resource descriptors, graph slug, and resource instance ID to an Excel file.",
                        )
                    }}
                </p>
            </div>
        </div>

        <div class="panel-footer">
            <div class="filename-row">
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

            <div
                v-if="exportError"
                class="export-error"
            >
                <i class="pi pi-exclamation-triangle" />
                {{ exportError }}
            </div>

            <Button
                :label="downloadButtonLabel"
                icon="pi pi-download"
                icon-pos="left"
                :loading="isExporting"
                :disabled="
                    isExporting || searchResults.pagination.total_results === 0
                "
                class="download-btn"
                @click="onExport"
            />
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

.panel-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.8rem;
}

.item-meta {
    font-size: 0.85em;
    color: var(--p-surface-500);
    margin-bottom: 0.6rem;
}

.export-item {
    padding: 0.6rem;
    border: 0.0625rem solid var(--p-content-border-color);
    border-radius: 0.25rem;
    cursor: pointer;
}

.export-item:hover {
    background-color: var(--p-surface-50);
}

.item-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.3rem;
}

.item-name {
    font-weight: 600;
    cursor: pointer;
}

.item-description {
    margin: 0 0 0 1.5rem;
    color: var(--p-surface-500);
    font-size: 0.85em;
}

.panel-footer {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0.8rem;
    border-top: 0.125rem solid var(--p-content-border-color);
}

.filename-row {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}

.form-label {
    font-weight: 500;
    font-size: var(--p-arches-search-font-size);
}

:deep(.filter-input .p-inputtext),
:deep(.filter-input) {
    font-size: var(--p-arches-search-font-size);
}

.export-error {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--p-red-500);
}

.download-btn {
    align-self: flex-end;
    font-size: var(--p-arches-search-font-size);
}
</style>
