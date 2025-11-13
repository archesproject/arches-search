<script setup lang="ts">
import { computed, defineEmits, defineProps } from "vue";
import { useGettext } from "vue3-gettext";
import SelectButton from "primevue/selectbutton";

type ClauseTypeToken = "LITERAL" | "RELATED";
type ClauseQuantifierToken = "ANY" | "ALL" | "NONE";
type OperandPayloadTypeToken = "LITERAL" | "PATH";

const { $gettext } = useGettext();

const props = defineProps<{
    clauseType: ClauseTypeToken;
    quantifier: ClauseQuantifierToken;
    operandType: OperandPayloadTypeToken;
    clauseTypeOptions: { label: string; value: ClauseTypeToken }[];
    clauseQuantifierOptions: { label: string; value: ClauseQuantifierToken }[];
    operandTypeOptions: { label: string; value: OperandPayloadTypeToken }[];
}>();

const emit = defineEmits<{
    (event: "update:clause-type", nextClauseType: ClauseTypeToken): void;
    (event: "update:quantifier", nextQuantifier: ClauseQuantifierToken): void;
    (
        event: "update:operand-type",
        nextOperandType: OperandPayloadTypeToken,
    ): void;
}>();

const selectedClauseType = computed<ClauseTypeToken>({
    get(): ClauseTypeToken {
        return props.clauseType;
    },
    set(nextClauseType: ClauseTypeToken): void {
        if (nextClauseType === props.clauseType) {
            return;
        }
        emit("update:clause-type", nextClauseType);
    },
});

const selectedQuantifier = computed<ClauseQuantifierToken>({
    get(): ClauseQuantifierToken {
        return props.quantifier;
    },
    set(nextQuantifier: ClauseQuantifierToken): void {
        if (nextQuantifier === props.quantifier) {
            return;
        }
        emit("update:quantifier", nextQuantifier);
    },
});

const selectedOperandType = computed<OperandPayloadTypeToken>({
    get(): OperandPayloadTypeToken {
        return props.operandType;
    },
    set(nextOperandType: OperandPayloadTypeToken): void {
        if (nextOperandType === props.operandType) {
            return;
        }
        emit("update:operand-type", nextOperandType);
    },
});
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
                    v-model="selectedClauseType"
                    :options="clauseTypeOptions"
                    option-label="label"
                    option-value="value"
                    :allow-empty="false"
                    class="clause-advanced-select"
                />
            </div>

            <div class="clause-advanced-option">
                <div class="clause-advanced-label">
                    {{ $gettext("Quantifier") }}
                </div>

                <SelectButton
                    v-model="selectedQuantifier"
                    :options="clauseQuantifierOptions"
                    option-label="label"
                    option-value="value"
                    :allow-empty="false"
                    class="clause-advanced-select"
                />
            </div>

            <div class="clause-advanced-option">
                <div class="clause-advanced-label">
                    {{ $gettext("Operand value type") }}
                </div>

                <SelectButton
                    v-model="selectedOperandType"
                    :options="operandTypeOptions"
                    option-label="label"
                    option-value="value"
                    :allow-empty="false"
                    class="clause-advanced-select"
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
    padding: 0.85rem 1rem;
    border-radius: 0.75rem;
    border: 0.0625rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    font-size: 1.2rem;
}

.clause-advanced-header {
    display: flex;
    align-items: center;
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
    border-bottom: 0.0625rem solid var(--p-content-border-color);
}

.clause-advanced-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--p-text-color-secondary);
    text-transform: uppercase;
    letter-spacing: 0.06em;
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
    min-width: 14rem;
}

.clause-advanced-label {
    font-size: 1.1rem;
    font-weight: 500;
}

.clause-advanced-select {
    min-width: 14rem;
}
</style>
