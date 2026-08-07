<script setup lang="ts">
import { ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import InputText from "primevue/inputtext";
import Message from "primevue/message";

import { parseNumericFilter } from "@/arches_search/SimpleSearch/components/attribute-filters/numeric-parser.ts";

import type { NodeFilterConfigNode } from "@/arches_search/SimpleSearch/types.ts";
import type { NumericFilterValue } from "@/arches_search/SimpleSearch/components/attribute-filters/types.ts";
import type { NumericParseError } from "@/arches_search/SimpleSearch/components/attribute-filters/numeric-parser.ts";

const { $gettext } = useGettext();

const props = defineProps<{
    node: NodeFilterConfigNode;
    modelValue: NumericFilterValue | null;
}>();

const emit = defineEmits<{
    (event: "update:modelValue", value: NumericFilterValue): void;
}>();

const text = ref(props.modelValue?.text ?? "");
const errorMessage = ref<string | null>(null);

// Re-sync when the value is reset externally (e.g. switching graphs clears it).
watch(
    () => props.modelValue?.text ?? "",
    (incoming) => {
        if (incoming !== text.value) {
            text.value = incoming;
        }
    },
);

// Validate on every change. Invalid input shows an inline error and is *not*
// emitted, so the previously-applied filter stays put until the user fixes it.
// Empty input parses to zero tokens, which clears the filter downstream.
watch(text, (value) => {
    const { tokens, error } = parseNumericFilter(value);
    if (error) {
        errorMessage.value = messageForError(error);
        return;
    }
    errorMessage.value = null;
    emit("update:modelValue", { text: value, tokens });
});

function messageForError(error: NumericParseError): string {
    switch (error.code) {
        case "RANGE_ORDER":
            return $gettext('Range "%{token}" must be written low-high.', {
                token: error.token,
            });
        case "MALFORMED_RANGE":
            return $gettext('"%{token}" is not a valid range.', {
                token: error.token,
            });
        default:
            return $gettext('"%{token}" is not a valid number or range.', {
                token: error.token,
            });
    }
}
</script>

<template>
    <div class="numeric-filter">
        <InputText
            v-model="text"
            class="numeric-input"
            fluid
            :invalid="errorMessage !== null"
            :placeholder="$gettext('e.g. 9-10, 12')"
            :aria-label="node.label"
        />
        <Message
            v-if="errorMessage"
            severity="error"
            size="small"
            variant="simple"
        >
            {{ errorMessage }}
        </Message>
        <small
            v-else
            class="numeric-hint"
        >
            {{ $gettext("Enter values or ranges separated by commas.") }}
        </small>
    </div>
</template>

<style scoped>
.numeric-filter {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.4rem 0 0.8rem 0;
}

.numeric-input {
    width: 100%;
}

.numeric-hint {
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    line-height: 1.5;
    margin: 0;
}
</style>
