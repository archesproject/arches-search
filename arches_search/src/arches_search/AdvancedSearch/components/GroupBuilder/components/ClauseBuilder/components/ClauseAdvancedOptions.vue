<script setup lang="ts">
import { useGettext } from "vue3-gettext";
import SelectButton from "primevue/selectbutton";

type ClauseTypeToken = "LITERAL" | "RELATED";
type OperandPayloadTypeToken = "LITERAL" | "PATH";

const { $gettext } = useGettext();

const { clauseType, operandType, clauseTypeOptions, operandTypeOptions } =
    defineProps<{
        clauseType: ClauseTypeToken;
        operandType: OperandPayloadTypeToken;
        clauseTypeOptions: { label: string; value: ClauseTypeToken }[];
        operandTypeOptions: { label: string; value: OperandPayloadTypeToken }[];
    }>();

const emit = defineEmits<{
    (event: "update:clause-type", nextClauseType: ClauseTypeToken): void;
    (
        event: "update:operand-type",
        nextOperandType: OperandPayloadTypeToken,
    ): void;
}>();

function onChangeClauseType(nextClauseType: ClauseTypeToken): void {
    if (nextClauseType === clauseType) {
        return;
    }
    emit("update:clause-type", nextClauseType);
}

function onChangeOperandType(nextOperandType: OperandPayloadTypeToken): void {
    if (nextOperandType === operandType) {
        return;
    }
    emit("update:operand-type", nextOperandType);
}
</script>

<template>
    <div class="clause-advanced-card">
        <div class="clause-advanced-header">
            <span class="clause-advanced-title">
                {{ $gettext("Advanced options") }}
            </span>
        </div>

        <div class="clause-advanced-body">
            <div class="clause-advanced-option">
                <div class="clause-advanced-label">
                    {{ $gettext("Relationship type") }}
                </div>

                <SelectButton
                    :model-value="clauseType"
                    :options="clauseTypeOptions"
                    option-label="label"
                    option-value="value"
                    :allow-empty="false"
                    class="clause-advanced-select"
                    @update:model-value="onChangeClauseType"
                />
            </div>

            <div class="clause-advanced-option">
                <div class="clause-advanced-label">
                    {{ $gettext("Operand value type") }}
                </div>

                <SelectButton
                    :model-value="operandType"
                    :options="operandTypeOptions"
                    option-label="label"
                    option-value="value"
                    :allow-empty="false"
                    class="clause-advanced-select"
                    @update:model-value="onChangeOperandType"
                />
            </div>
        </div>
    </div>
</template>

<style scoped>
.clause-advanced-card {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 1rem;
    border-radius: 0.75rem;
    border: 0.125rem solid var(--p-content-border-color);
    background: var(--p-content-background);
}

.clause-advanced-header {
    display: flex;
    align-items: center;
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 0.125rem solid var(--p-content-border-color);
}

.clause-advanced-title {
    color: var(--p-text-color-secondary);
    text-transform: uppercase;
}

.clause-advanced-body {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.5rem;
}

.clause-advanced-option {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
</style>
