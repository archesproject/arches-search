<script setup lang="ts">
import { computed, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import RadioButton from "primevue/radiobutton";
import ToggleSwitch from "primevue/toggleswitch";

import { exportSearchResults } from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

defineProps<{
    visible: boolean;
}>();

const emit = defineEmits<{
    (event: "update:visible", value: boolean): void;
}>();

const { $gettext } = useGettext();
const { searchResults, getExportPayload } = useSearchFilters();

const isExporting = ref(false);
const exportError = ref<string | null>(null);
const filename = ref("search_export");
const selectedFormat = ref("simple");
const allDescriptors = ref(false);

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
            allDescriptors: allDescriptors.value,
        });
        emit("update:visible", false);
    } catch (error) {
        exportError.value =
            error instanceof Error ? error.message : $gettext("Export failed");
    } finally {
        isExporting.value = false;
    }
}
</script>

<template>
    <Dialog
        :visible="visible"
        :header="$gettext('Export Results')"
        modal
        :closable="true"
        class="export-panel"
        @update:visible="$emit('update:visible', $event)"
    >
        <div class="panel-list">
            <div class="item-meta">
                <i class="pi pi-database" />
                <span class="item-type">
                    {{
                        $gettext("%{count} results will be exported", {
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
                        {{ $gettext("Export Results") }}
                    </label>
                </div>
                <div class="item-description">
                    {{
                        $gettext(
                            "Export resource name and descriptions to an Excel file.",
                        )
                    }}
                </div>
                <div class="descriptors-toggle">
                    <ToggleSwitch
                        v-model="allDescriptors"
                        input-id="all-descriptors-toggle"
                    />
                    <label for="all-descriptors-toggle">
                        {{ $gettext("Export all descriptors") }}
                    </label>
                </div>
            </div>

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
        </div>

        <template #footer>
            <Button
                :label="$gettext('Cancel')"
                severity="secondary"
                @click="$emit('update:visible', false)"
            />
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
        </template>
    </Dialog>
</template>

<style scoped>
.export-panel {
    width: 44rem;
    max-width: 90vw;
}

:deep(.p-dialog-content) {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.panel-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.item-meta {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.625rem 0.75rem;
    background: var(--p-surface-100);
    border-radius: 0.6rem;
    font-size: 1.3rem;
    color: var(--p-text-color);
}

.item-meta .pi {
    color: var(--p-primary-color);
}

.export-item {
    padding: 0.625rem 0.75rem;
    border: 0.125rem solid var(--p-content-border-color);
    border-radius: 0.4375rem;
    background: var(--arches-search-page-bg);
    cursor: pointer;
    transition:
        border-color 0.12s,
        background 0.12s;
}

.export-item:hover {
    border-color: var(--p-primary-color);
    background: var(--p-primary-50);
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
    margin-inline-start: 1.5rem;
    color: var(--p-text-muted-color);
    font-size: 0.85em;
}

.descriptors-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-block-start: 0.5rem;
    margin-inline-start: 1.5rem;
    font-size: 0.85em;
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
