<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import InputText from "openvue/inputtext";
import RadioButton from "openvue/radiobutton";

import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import {
    EXPORT_CONCEPTS_AS_LABELS,
    EXPORT_CONCEPTS_AS_UUIDS,
    EXPORT_FORMAT_BRANCH_EXCEL,
    EXPORT_FORMAT_TILE_EXCEL,
    EXPORT_STATE_IDLE,
    EXPORT_STATE_PENDING,
} from "@/arches_search/SimpleSearch/types.ts";
import type {
    ExportConceptsAs,
    ExportFormat,
    ExportRequest,
    ExportState,
} from "@/arches_search/SimpleSearch/types.ts";

const CLOSE_EVENT = "close" as const;
const EXPORT_EVENT = "export" as const;

const { hasSingleGraph = true, exportState = EXPORT_STATE_IDLE } = defineProps<{
    // Both Bulk Data Manager exporters operate on a single resource model.
    hasSingleGraph?: boolean;
    exportState?: ExportState;
}>();

const emit = defineEmits<{
    (event: "export", request: ExportRequest): void;
    (event: "close"): void;
}>();

const { $gettext } = useGettext();
const { searchResults } = useSearchFilters();

const selectedFormat = ref<ExportFormat>(EXPORT_FORMAT_BRANCH_EXCEL);
const exportConceptsAs = ref<ExportConceptsAs>(EXPORT_CONCEPTS_AS_LABELS);
const filename = ref("search_export");

const totalResults = computed<number>(
    () => searchResults.value.pagination?.total_results ?? 0,
);

const formatOptions = computed(() => [
    {
        value: EXPORT_FORMAT_BRANCH_EXCEL,
        label: $gettext("Branch Excel"),
    },
    {
        value: EXPORT_FORMAT_TILE_EXCEL,
        label: $gettext("Tile Excel"),
    },
]);

const isExporting = computed<boolean>(
    () => exportState === EXPORT_STATE_PENDING,
);

const canExport = computed<boolean>(
    () =>
        hasSingleGraph &&
        !isExporting.value &&
        totalResults.value > 0 &&
        filename.value.trim() !== "",
);

watch(
    () => hasSingleGraph,
    (isSingle) => {
        if (!isSingle) {
            selectedFormat.value = EXPORT_FORMAT_BRANCH_EXCEL;
        }
    },
);

function onExport(): void {
    if (!canExport.value) return;
    emit(EXPORT_EVENT, {
        format: selectedFormat.value,
        filename: filename.value.trim(),
        exportConceptsAs: exportConceptsAs.value,
    });
}
</script>

<template>
    <div class="export-results-panel">
        <div class="panel-header">
            <span class="panel-header-title">
                <i class="pi pi-download" />
                {{ $gettext("Export Search Results") }}
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

        <div class="export-form">
            <div class="export-summary">
                <i class="pi pi-database" />
                <span>
                    {{
                        $gettext("%{count} results will be exported", {
                            count: String(totalResults),
                        })
                    }}
                </span>
            </div>

            <div
                v-if="!hasSingleGraph"
                class="export-notice"
            >
                <i class="pi pi-info-circle" />
                <span>
                    {{
                        $gettext(
                            "Select a single resource type to export results.",
                        )
                    }}
                </span>
            </div>

            <fieldset
                class="export-field"
                :disabled="!hasSingleGraph"
            >
                <legend class="export-label">
                    {{ $gettext("Format") }}
                </legend>
                <label
                    v-for="option in formatOptions"
                    :key="option.value"
                    :for="`export-format-${option.value}`"
                    class="format-option"
                    :class="{ selected: selectedFormat === option.value }"
                >
                    <span class="format-option-header">
                        <RadioButton
                            v-model="selectedFormat"
                            name="exportFormat"
                            :input-id="`export-format-${option.value}`"
                            :value="option.value"
                        />
                        <span class="format-option-name">
                            {{ option.label }}
                        </span>
                    </span>
                </label>
            </fieldset>

            <fieldset
                v-if="selectedFormat === EXPORT_FORMAT_TILE_EXCEL"
                class="export-field"
                :disabled="!hasSingleGraph"
            >
                <legend class="export-label">
                    {{ $gettext("Export concepts as") }}
                </legend>
                <div class="concepts-options">
                    <span class="concepts-option">
                        <RadioButton
                            v-model="exportConceptsAs"
                            name="exportConceptsAs"
                            input-id="export-concepts-labels"
                            :value="EXPORT_CONCEPTS_AS_LABELS"
                        />
                        <label for="export-concepts-labels">
                            {{ $gettext("Labels") }}
                        </label>
                    </span>
                    <span class="concepts-option">
                        <RadioButton
                            v-model="exportConceptsAs"
                            name="exportConceptsAs"
                            input-id="export-concepts-uuids"
                            :value="EXPORT_CONCEPTS_AS_UUIDS"
                        />
                        <label for="export-concepts-uuids">
                            {{ $gettext("UUIDs") }}
                        </label>
                    </span>
                </div>
            </fieldset>

            <div class="export-field">
                <label
                    for="export-filename"
                    class="export-label"
                >
                    {{ $gettext("File name") }}
                </label>
                <InputText
                    id="export-filename"
                    v-model="filename"
                    class="export-input"
                    :fluid="true"
                    :disabled="!hasSingleGraph"
                    @keydown.enter="onExport"
                />
            </div>

            <div class="export-actions">
                <Button
                    icon="pi pi-download"
                    :label="
                        isExporting
                            ? $gettext('Exporting...')
                            : $gettext('Export')
                    "
                    :loading="isExporting"
                    :disabled="!canExport"
                    @click="onExport"
                />
            </div>
        </div>
    </div>
</template>

<style scoped>
.export-results-panel {
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

.export-form {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 2rem;
    overflow-y: auto;
}

.export-summary,
.export-notice {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.8rem 1.2rem;
    border-radius: 0.6rem;
    font-size: 1.3rem;
    color: var(--p-text-color);
}

.export-summary {
    background: var(--p-surface-100);
}

.export-summary .pi,
.export-notice .pi {
    color: var(--p-primary-color);
}

.export-notice {
    border: 0.1rem solid var(--p-content-border-color);
    background: var(--arches-search-page-bg);
}

.export-field {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin: 0;
    padding: 0;
    border: none;
    min-inline-size: 0;
}

.export-label {
    padding: 0;
    margin-block-end: 0.2rem;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--p-text-muted-color);
    text-transform: uppercase;
    letter-spacing: 0.048rem;
}

:deep(.export-input .p-inputtext),
:deep(.export-input) {
    font-size: var(--p-arches-search-font-size);
}

.format-option {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.625rem 0.75rem;
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.5rem;
    background: var(--arches-search-page-bg);
    cursor: pointer;
    transition:
        border-color 0.12s,
        box-shadow 0.12s;
}

.format-option:hover,
.format-option.selected {
    border-color: var(--p-primary-color);
}

.format-option:hover {
    box-shadow: var(--arches-search-item-hover-shadow);
}

.export-field:disabled .format-option {
    cursor: not-allowed;
    opacity: 0.6;
}

.format-option-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}

.format-option-name {
    font-weight: 600;
    color: var(--p-text-color);
}

.concepts-options {
    display: flex;
    gap: 2rem;
}

.concepts-option {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
}

.concepts-option label {
    cursor: pointer;
}

.export-actions {
    display: flex;
    gap: 0.8rem;
}
</style>
