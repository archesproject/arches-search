<script setup lang="ts">
import {
    defineOptions,
    defineProps,
    defineEmits,
    computed,
    ref,
    watch,
} from "vue";
import Select from "primevue/select";
import Button from "primevue/button";
import type { Clause } from "@/arches_search/AdvancedSearch/utils/query-tree.ts";
import { setClauseNodeAlias } from "@/arches_search/AdvancedSearch/utils/query-tree.ts";

defineOptions({ name: "QueryClause" });

type GraphNodeOption = { [key: string]: unknown };
type QueryRenderConfig = { nodeLabelKey?: string; nodeValueKey?: string };

const props = defineProps<{
    clause: Clause;
    nodes: GraphNodeOption[];
    config?: QueryRenderConfig;
}>();

const emit = defineEmits<{
    (e: "request-remove-clause", targetClause: Clause): void;
}>();

const optionLabelKey = computed(() => props.config?.nodeLabelKey ?? "name");
const optionValueKey = computed(
    () => props.config?.nodeValueKey ?? "node_alias",
);

const selectedNodeAlias = ref<string | null>(props.clause.node_alias ?? null);

watch(selectedNodeAlias, (nextAlias) => {
    setClauseNodeAlias(props.clause, nextAlias ?? null);
});

watch(
    () => props.clause.node_alias,
    (nextAlias) => {
        if (nextAlias !== selectedNodeAlias.value) {
            selectedNodeAlias.value = nextAlias ?? null;
        }
    },
);

function onRemoveSelf() {
    emit("request-remove-clause", props.clause);
}
</script>

<template>
    <div class="query-clause">
        <div class="query-clause__row">
            <Select
                v-model="selectedNodeAlias"
                :options="nodes"
                :option-label="optionLabelKey"
                :option-value="optionValueKey"
                :placeholder="'Choose…'"
                class="query-clause__control"
            />
            <Button
                class="query-clause__remove"
                icon="pi pi-times"
                severity="danger"
                @click="onRemoveSelf"
            />
        </div>
    </div>
</template>

<style scoped>
.query-clause {
    border: 1px solid var(--p-content-border-color);
    border-radius: var(--p-content-border-radius);
    padding: 12px;
    background: var(--p-content-background);
    color: var(--p-text-color);
}
.query-clause__row {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 8px;
}
.query-clause__control {
    width: 100%;
}
</style>
