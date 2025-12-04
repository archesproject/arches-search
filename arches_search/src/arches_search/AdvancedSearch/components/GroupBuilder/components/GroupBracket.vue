<script setup lang="ts">
import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";

const { $gettext } = useGettext();

const { show, logic } = defineProps<{
    show: boolean;
    logic: LogicToken;
}>();

const emit = defineEmits<{
    (event: "update:logic", value: LogicToken): void;
}>();

const currentLogicLabel = computed<string>(() => {
    if (logic === LogicToken.AND) {
        return $gettext("AND");
    }
    return $gettext("OR");
});

function onToggle(): void {
    const nextLogic = logic === LogicToken.AND ? LogicToken.OR : LogicToken.AND;
    emit("update:logic", nextLogic);
}
</script>

<template>
    <div
        v-if="show"
        class="bracket"
        :data-logic="logic"
    >
        <div class="bracket-arm bracket-arm-top"></div>
        <div class="bracket-spine bracket-spine-top"></div>

        <div class="bracket-lane">
            <Button
                :label="currentLogicLabel"
                class="bracket-logic"
                size="small"
                @click.stop="onToggle"
            />
        </div>

        <div class="bracket-spine bracket-spine-bottom"></div>
        <div class="bracket-arm bracket-arm-bottom"></div>
    </div>
</template>

<style scoped>
.bracket {
    --spine-thickness: 0.25rem;
    --arm-thickness: 0.25rem;
    --lane-width: 0.25rem;
    --gap-inline: 0.75rem;
    --button-col: 1.5rem;

    display: grid;
    grid-template-columns: var(--lane-width) var(--button-col);
    grid-template-rows: 1fr auto 1fr;
    row-gap: 0.5rem;
}

.bracket[data-logic="AND"] {
    --logic-color: var(--p-blue-600);
    --logic-hover-color: var(--p-blue-700);
}

.bracket[data-logic="OR"] {
    --logic-color: var(--p-orange-600);
    --logic-hover-color: var(--p-orange-700);
}

.bracket-spine,
.bracket-arm {
    margin-inline-start: var(--gap-inline);
    background: var(--logic-color);
}

.bracket-spine {
    grid-column: 1;
    width: var(--spine-thickness);
    align-self: stretch;
}

.bracket-spine-top {
    grid-row: 1;
}

.bracket-spine-bottom {
    grid-row: 3;
}

.bracket-arm {
    grid-column: 2;
    width: 100%;
    height: var(--arm-thickness);
}

.bracket-arm-top {
    grid-row: 1;
    align-self: start;
}

.bracket-arm-bottom {
    grid-row: 3;
    align-self: end;
}

.bracket-lane {
    grid-column: 1;
    grid-row: 2;
    display: grid;
    place-items: center;
    width: var(--lane-width);
}

.bracket-logic.p-button {
    background: var(--logic-color);
    border-color: var(--logic-color);
    color: var(--p-surface-0);
    padding-block: 0.25rem;
    padding-inline: 0.75rem;
}

.bracket-logic.p-button:enabled:hover {
    background: var(--logic-hover-color);
    border-color: var(--logic-hover-color);
    color: var(--p-surface-0);
}
</style>
