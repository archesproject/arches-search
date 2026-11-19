<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import InputText from "openvue/inputtext";
import RadioButton from "openvue/radiobutton";
import Textarea from "openvue/textarea";

import { useToast } from "openvue/usetoast";
import {
    createSavedSearch,
    getResourceSetLimits,
    saveResultsAsResourceSet,
} from "@/arches_search/SimpleSearch/api.ts";

import type {
    ResourceSetLimits,
    SearchDefinition,
    SearchResultsToSave,
} from "@/arches_search/SimpleSearch/types.ts";

const SAVE_AS_QUERY = "query" as const;
const SAVE_AS_RESULTS = "results" as const;

const {
    definitionToSave = null,
    resultsToSave = null,
    resultCount = 0,
} = defineProps<{
    definitionToSave?: SearchDefinition | null;
    // Given, the form can also save the results as a resource set.
    resultsToSave?: SearchResultsToSave | null;
    resultCount?: number;
}>();

const { $gettext } = useGettext();
const toast = useToast();

const saveAs = ref<typeof SAVE_AS_QUERY | typeof SAVE_AS_RESULTS>(
    SAVE_AS_QUERY,
);
const saveSearchName = ref("");
const saveSearchDescription = ref("");
const isSaving = ref(false);
const resourceSetLimits = ref<ResourceSetLimits | null>(null);

const isSavingResults = computed<boolean>(
    () => saveAs.value === SAVE_AS_RESULTS,
);

const isOverMemberLimit = computed<boolean>(
    () =>
        resourceSetLimits.value !== null &&
        resultCount > resourceSetLimits.value.member_limit,
);

const isSavedInBackground = computed<boolean>(
    () =>
        resourceSetLimits.value !== null &&
        resultCount > resourceSetLimits.value.immediate_threshold,
);

const isSaveDisabled = computed<boolean>(
    () =>
        isSaving.value ||
        saveSearchName.value.trim() === "" ||
        (isSavingResults.value
            ? resultsToSave === null ||
              resultCount === 0 ||
              isOverMemberLimit.value
            : definitionToSave === null),
);

// The limits decide the notices shown before saving results.
watch(saveAs, async (value) => {
    if (value !== SAVE_AS_RESULTS || resourceSetLimits.value !== null) {
        return;
    }
    try {
        resourceSetLimits.value = await getResourceSetLimits();
    } catch {
        // e.g. not signed in; the save itself still checks the limits.
    }
});

function resetForm(): void {
    saveSearchName.value = "";
    saveSearchDescription.value = "";
}

async function onSaveSearch(): Promise<void> {
    const name = saveSearchName.value.trim();
    if (!name || !definitionToSave) {
        return;
    }

    isSaving.value = true;
    try {
        await createSavedSearch(
            name,
            saveSearchDescription.value.trim(),
            definitionToSave,
        );
        resetForm();
        toast.add({
            severity: "success",
            life: 3000,
            summary: $gettext("Search saved"),
        });
    } catch (error) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("Failed to save search"),
            detail: (error as Error).message,
        });
    } finally {
        isSaving.value = false;
    }
}

async function onSaveResults(): Promise<void> {
    if (isSaveDisabled.value || !resultsToSave) {
        return;
    }

    isSaving.value = true;
    try {
        const saved = await saveResultsAsResourceSet({
            ...resultsToSave,
            name: saveSearchName.value.trim(),
            description: saveSearchDescription.value.trim(),
        });
        resetForm();
        toast.add({
            severity: "success",
            life: saved.task_id ? 5000 : 3000,
            summary: saved.task_id
                ? $gettext("Saving results")
                : $gettext("Results saved"),
            detail: saved.message,
        });
    } catch (error) {
        toast.add({
            severity: "error",
            life: 5000,
            summary: $gettext("Failed to save results"),
            detail: (error as Error).message,
        });
    } finally {
        isSaving.value = false;
    }
}
</script>

<template>
    <div class="save-form">
        <fieldset
            v-if="resultsToSave !== null"
            class="save-as-field"
            :aria-label="$gettext('Save as')"
        >
            <span class="save-as-option">
                <RadioButton
                    v-model="saveAs"
                    name="saveAs"
                    input-id="save-as-query"
                    :value="SAVE_AS_QUERY"
                />
                <label for="save-as-query">
                    {{ $gettext("Saved search query") }}
                </label>
            </span>
            <span class="save-as-option">
                <RadioButton
                    v-model="saveAs"
                    name="saveAs"
                    input-id="save-as-results"
                    :value="SAVE_AS_RESULTS"
                />
                <label for="save-as-results">
                    {{ $gettext("Static set") }}
                </label>
            </span>
        </fieldset>
        <p class="save-form-hint">
            {{
                isSavingResults
                    ? $gettext(
                          "Save the resources this search matches now. The saved results won't change when records are added or edited later.",
                      )
                    : $gettext(
                          "Give this search a name to save it to your account.",
                      )
            }}
        </p>
        <template v-if="isSavingResults">
            <div
                v-if="resultCount === 0"
                class="save-notice"
            >
                <i class="pi pi-info-circle" />
                <span>{{ $gettext("There are no results to save.") }}</span>
            </div>
            <div
                v-else-if="isOverMemberLimit && resourceSetLimits"
                class="save-notice save-notice-error"
            >
                <i class="pi pi-exclamation-triangle" />
                <span>
                    {{
                        $gettext(
                            "This search matches %{count} resources, more than the limit of %{limit}. Narrow the search to save its results.",
                            {
                                count: String(resultCount),
                                limit: String(resourceSetLimits.member_limit),
                            },
                        )
                    }}
                </span>
            </div>
            <div
                v-else
                class="save-notice"
            >
                <i class="pi pi-database" />
                <span>
                    {{
                        isSavedInBackground
                            ? $gettext(
                                  "%{count} results will be saved in the background. You will be notified when they are ready.",
                                  { count: String(resultCount) },
                              )
                            : $gettext("%{count} results will be saved", {
                                  count: String(resultCount),
                              })
                    }}
                </span>
            </div>
        </template>
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
                @keydown.enter="
                    isSavingResults ? onSaveResults() : onSaveSearch()
                "
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
                :disabled="isSaveDisabled"
                @click="isSavingResults ? onSaveResults() : onSaveSearch()"
            />
        </div>
    </div>
</template>

<style scoped>
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

.save-as-field {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    margin: 0;
    padding: 0;
    border: none;
    min-inline-size: 0;
}

.save-as-option {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
}

.save-notice {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.8rem 1.2rem;
    border-radius: 0.6rem;
    font-size: 1.3rem;
    color: var(--p-text-color);
    background: var(--p-surface-100);
}

.save-notice .pi {
    color: var(--p-primary-color);
}

.save-notice-error .pi {
    color: var(--p-red-500);
}

.save-form-actions {
    display: flex;
    gap: 0.8rem;
}
</style>
