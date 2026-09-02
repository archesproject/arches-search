<script setup lang="ts">
import { ref, watchEffect } from "vue";
import { useGettext } from "vue3-gettext";

import Checkbox from "primevue/checkbox";
import InputText from "primevue/inputtext";
import Select from "primevue/select";

import { fetchResourceFieldMetadata } from "@/arches_search/SimpleSearch/api.ts";
import { useSearchFilters } from "@/arches_search/SimpleSearch/composables/useSearchFilters.ts";

import type {
    ResourceFieldMetadata,
    ResourceFieldChoice,
} from "@/arches_search/SimpleSearch/types.ts";

const OPERATOR_IN = "IN";
const OPERATOR_CONTAINS = "CONTAINS";
const OPERATOR_IS_CURRENT_USER = "IS_CURRENT_USER";

const KIND_CHOICE = "CHOICE";
const KIND_USER = "USER";
const KIND_TEXT = "TEXT";

const { $gettext } = useGettext();
const { activeGraphs, setResourceFieldFilter } = useSearchFilters();

const fields = ref<ResourceFieldMetadata[]>([]);
const loadError = ref<string | null>(null);

const choiceSelections = ref<Record<string, string | null>>({});
const textSelections = ref<Record<string, string>>({});
const onlyMineSelections = ref<Record<string, boolean>>({});

watchEffect(async () => {
    const graphIds = activeGraphs.value.map((graph) => graph.id as string);
    try {
        fields.value = await fetchResourceFieldMetadata(graphIds);
        loadError.value = null;
    } catch (error) {
        loadError.value = (error as Error).message;
        fields.value = [];
    }
});

function supports(field: ResourceFieldMetadata, operator: string): boolean {
    return field.operators.includes(operator);
}

function choicesFor(field: ResourceFieldMetadata): ResourceFieldChoice[] {
    return field.choices ?? [];
}

function onChoiceChange(field: ResourceFieldMetadata, value: string | null) {
    choiceSelections.value[field.field] = value;
    setResourceFieldFilter(
        field.field,
        value
            ? { field: field.field, operator: OPERATOR_IN, value: [value] }
            : null,
    );
}

function onTextChange(field: ResourceFieldMetadata, value: string) {
    textSelections.value[field.field] = value;
    setResourceFieldFilter(
        field.field,
        value
            ? { field: field.field, operator: OPERATOR_CONTAINS, value }
            : null,
    );
}

function onOnlyMineChange(field: ResourceFieldMetadata, checked: boolean) {
    onlyMineSelections.value[field.field] = checked;
    // IS_CURRENT_USER carries no value; the server resolves the identity.
    setResourceFieldFilter(
        field.field,
        checked
            ? { field: field.field, operator: OPERATOR_IS_CURRENT_USER }
            : null,
    );
}
</script>

<template>
    <div class="resource-field-filters">
        <p
            v-if="loadError"
            class="resource-field-filters-error"
        >
            {{ $gettext("Record filters could not be loaded.") }}
        </p>
        <template v-else>
            <div
                v-for="field in fields"
                :key="field.field"
                class="resource-field-filters-field"
            >
                <label
                    class="resource-field-filters-label"
                    :for="`resource-field-${field.field}`"
                >
                    {{ field.label }}
                </label>

                <Select
                    v-if="
                        field.kind === KIND_CHOICE &&
                        choicesFor(field).length > 0
                    "
                    :input-id="`resource-field-${field.field}`"
                    :model-value="choiceSelections[field.field] ?? null"
                    :options="choicesFor(field)"
                    option-label="label"
                    option-value="value"
                    :show-clear="true"
                    :placeholder="$gettext('Any')"
                    @update:model-value="onChoiceChange(field, $event)"
                />

                <div
                    v-else-if="
                        field.kind === KIND_USER &&
                        supports(field, OPERATOR_IS_CURRENT_USER)
                    "
                    class="resource-field-filters-checkbox"
                >
                    <Checkbox
                        :input-id="`resource-field-${field.field}`"
                        :model-value="onlyMineSelections[field.field] ?? false"
                        :binary="true"
                        @update:model-value="onOnlyMineChange(field, $event)"
                    />
                    <span>{{ $gettext("Only records I created") }}</span>
                </div>

                <InputText
                    v-else-if="
                        field.kind === KIND_TEXT &&
                        supports(field, OPERATOR_CONTAINS)
                    "
                    :id="`resource-field-${field.field}`"
                    :model-value="textSelections[field.field] ?? ''"
                    :placeholder="$gettext('Contains…')"
                    @update:model-value="onTextChange(field, $event ?? '')"
                />
            </div>
        </template>
    </div>
</template>

<style scoped>
.resource-field-filters {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.resource-field-filters .resource-field-filters-field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.resource-field-filters .resource-field-filters-label {
    font-size: 0.8rem;
    color: var(--p-text-muted-color);
}

.resource-field-filters .resource-field-filters-checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.resource-field-filters .resource-field-filters-error {
    color: var(--p-text-muted-color);
}
</style>
