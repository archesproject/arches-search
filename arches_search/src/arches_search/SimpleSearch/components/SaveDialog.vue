<script setup lang="ts">
import { ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";

const { $gettext } = useGettext();

defineProps<{
    visible: boolean;
}>();

const emit = defineEmits<{
    (event: "update:visible", value: boolean): void;
    (event: "save", payload: { name: string; description: string }): void;
}>();

const queryName = ref("");
const description = ref("");

function onSave() {
    const name = queryName.value.trim();
    if (!name) return;
    emit("save", { name, description: description.value.trim() });
    queryName.value = "";
    description.value = "";
}

function onCancel() {
    queryName.value = "";
    description.value = "";
    emit("update:visible", false);
}
</script>

<template>
    <Dialog
        :visible="visible"
        :header="$gettext('Save Query')"
        modal
        :closable="true"
        class="save-dialog"
        @update:visible="$emit('update:visible', $event)"
    >
        <div class="save-form">
            <label
                for="save-query-name"
                class="form-label"
            >
                {{ $gettext("Query Name") }}
            </label>
            <InputText
                id="save-query-name"
                v-model="queryName"
                class="form-input"
                fluid
                @keydown.enter="onSave"
            />

            <label
                for="save-query-description"
                class="form-label"
            >
                {{ $gettext("Description") }}
            </label>
            <Textarea
                id="save-query-description"
                v-model="description"
                class="form-input"
                fluid
                rows="3"
            />
        </div>

        <template #footer>
            <div class="dialog-footer">
                <Button
                    :label="$gettext('Save')"
                    @click="onSave"
                />
                <Button
                    :label="$gettext('Cancel')"
                    severity="secondary"
                    @click="onCancel"
                />
            </div>
        </template>
    </Dialog>
</template>

<style scoped>
.save-form {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    min-width: 20rem;
}

.form-label {
    font-weight: 500;
    font-size: var(--p-arches-search-font-size);
}

:deep(.form-input .p-inputtext),
:deep(.form-input .p-textarea),
:deep(.form-input) {
    font-size: var(--p-arches-search-font-size);
}

.dialog-footer {
    display: flex;
    gap: 0.6rem;
    justify-content: flex-end;
}
</style>
