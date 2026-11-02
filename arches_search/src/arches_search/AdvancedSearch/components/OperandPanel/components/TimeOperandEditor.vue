<script setup lang="ts">
import { computed, inject, ref, watch } from "vue";
import { useGettext } from "vue3-gettext";

import DatePicker from "openvue/datepicker";
import Message from "openvue/message";
import Select from "openvue/select";

import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";
import TimeSlider from "@/arches_search/SimpleSearch/components/TimeFilter/components/TimeSlider.vue";

import { getDateBoundsForGraphId } from "@/arches_search/AdvancedSearch/api.ts";
import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import { parseStoredDate } from "@/arches_search/AdvancedSearch/utils/advanced-search-payload-builder.ts";
import { toError } from "@/arches_search/AdvancedSearch/utils/errors.ts";
import { getClauseDatatype } from "@/arches_search/AdvancedSearch/utils/query-builder.ts";
import {
    addDays,
    clamp,
    countDaysBetween,
    parseSortableDate,
    toLocalISODateString,
} from "@/arches_search/SimpleSearch/components/TimeFilter/date-utils.ts";
import { ClauseSubjectTypeToken } from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    AdvancedSearchFacet,
    GraphModel,
    LiteralClause,
    LiteralOperand,
    Node,
} from "@/arches_search/AdvancedSearch/types.ts";

const UPDATE_CLAUSE_EVENT = "update:clause" as const;
const OPERAND_TYPE_LITERAL = "LITERAL" as const;
const OPERATOR_BETWEEN = "BETWEEN";
const RANGE_VALUE_COUNT = 2;
const PICKER_DATE_FORMAT = "yy-mm-dd";

const { clause } = defineProps<{
    clause: LiteralClause;
}>();

const emit = defineEmits<{
    (event: typeof UPDATE_CLAUSE_EVENT, updatedClause: LiteralClause): void;
}>();

const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;
const graphs = inject<Ref<GraphModel[]>>("graphs")!;
const getNodesForGraphId =
    inject<(graphId: string) => Promise<Node[]>>("getNodesForGraphId")!;

const { $gettext } = useGettext();
const queryBuilder = useQueryBuilder();

const sliderBounds = ref<[Date, Date] | null>(null);
const boundsError = ref<Error | null>(null);
const subjectNode = ref<Node | null>(null);
// The node widgets read their value only when mounted, so a slider change
// remounts them to show the dates it set.
const widgetRevision = ref(0);
const sliderOffsets = ref<[number, number] | null>(null);

const isNodeSubject = computed<boolean>(
    () => clause.subject.type === ClauseSubjectTypeToken.NODE,
);

const subjectGraph = computed<GraphModel | null>(
    () =>
        graphs.value.find(
            (graph) => graph.slug === clause.subject.graph_slug,
        ) ?? null,
);

const operatorOptions = computed<AdvancedSearchFacet[]>(() => {
    const datatype = getClauseDatatype(clause, queryBuilder.lookups);
    if (!datatype) {
        return [];
    }
    const facets = datatypesToAdvancedSearchFacets.value[datatype] ?? [];
    return facets.filter(
        (facet, facetIndex) =>
            facets.findIndex(
                (candidate) => candidate.operator === facet.operator,
            ) === facetIndex,
    );
});

const selectedFacet = computed<AdvancedSearchFacet | null>(
    () =>
        operatorOptions.value.find(
            (facet) => facet.operator === clause.operator,
        ) ?? null,
);

const valueCount = computed<number>(() => selectedFacet.value?.arity ?? 0);

const isRange = computed<boolean>(() => valueCount.value === RANGE_VALUE_COUNT);

const valueLabels = computed<string[]>(() => {
    if (isRange.value) {
        return [$gettext("From"), $gettext("To")];
    }
    return [$gettext("Date")];
});

watch(
    [subjectGraph, () => clause.subject.node_alias],
    async ([graph, nodeAlias], _previousSources, onCleanup) => {
        let isStale = false;
        onCleanup(() => {
            isStale = true;
        });
        sliderBounds.value = null;
        boundsError.value = null;
        subjectNode.value = null;
        if (!graph) {
            return;
        }
        const nodeAliases = nodeAlias ? [nodeAlias] : [];
        const [boundsResult, nodesResult] = await Promise.allSettled([
            getDateBoundsForGraphId(graph.graphid, nodeAliases),
            getNodesForGraphId(graph.graphid),
        ]);
        if (isStale) {
            return;
        }

        if (boundsResult.status === "rejected") {
            boundsError.value = toError(boundsResult.reason);
        } else if (
            boundsResult.value.min_value !== null &&
            boundsResult.value.max_value !== null
        ) {
            sliderBounds.value = [
                parseSortableDate(boundsResult.value.min_value),
                parseSortableDate(boundsResult.value.max_value),
            ];
            syncSlider(clause.operands);
        }

        if (nodesResult.status === "rejected") {
            console.error(nodesResult.reason);
        } else if (isNodeSubject.value) {
            subjectNode.value =
                nodesResult.value.find(
                    (node) =>
                        node.alias === nodeAlias && node.selectable !== false,
                ) ?? null;
        }
    },
    { immediate: true },
);

watch(
    operatorOptions,
    (options) => {
        const hasBetween = options.some(
            (facet) => facet.operator === OPERATOR_BETWEEN,
        );
        if (!clause.operator && hasBetween) {
            emit(UPDATE_CLAUSE_EVENT, {
                ...clause,
                operator: OPERATOR_BETWEEN,
                operands: [],
            });
        }
    },
    { immediate: true },
);

function storedDate(operandIndex: number): Date | null {
    return parseStoredDate(clause.operands[operandIndex]?.value);
}

function offsetsForOperands(
    operands: LiteralOperand[],
    bounds: [Date, Date],
): [number, number] {
    const totalDays = countDaysBetween(bounds[0], bounds[1]);
    const startDate = parseStoredDate(operands[0]?.value) ?? bounds[0];
    const endDate = parseStoredDate(operands[1]?.value) ?? bounds[1];
    return [
        clamp(countDaysBetween(bounds[0], startDate), 0, totalDays),
        clamp(countDaysBetween(bounds[0], endDate), 0, totalDays),
    ];
}

function syncSlider(operands: LiteralOperand[]): void {
    if (sliderBounds.value) {
        sliderOffsets.value = offsetsForOperands(operands, sliderBounds.value);
    }
}

function literalOperand(value: string): LiteralOperand {
    return { type: OPERAND_TYPE_LITERAL, value };
}

function onOperatorChange(nextOperator: string | null): void {
    if (!nextOperator || nextOperator === clause.operator) {
        return;
    }
    const nextArity =
        operatorOptions.value.find((facet) => facet.operator === nextOperator)
            ?.arity ?? 0;
    let operands = clause.operands;
    if (nextArity !== valueCount.value) {
        operands = [];
    }
    syncSlider(operands);
    emit(UPDATE_CLAUSE_EVENT, { ...clause, operator: nextOperator, operands });
}

function onSliderUpdate(offsets: [number, number]): void {
    const bounds = sliderBounds.value;
    if (!bounds) {
        return;
    }
    sliderOffsets.value = offsets;
    const earlierDate = addDays(bounds[0], Math.min(...offsets));
    const laterDate = addDays(bounds[0], Math.max(...offsets));
    widgetRevision.value += 1;
    emit(UPDATE_CLAUSE_EVENT, {
        ...clause,
        operands: [
            literalOperand(toLocalISODateString(earlierDate)),
            literalOperand(toLocalISODateString(laterDate)),
        ],
    });
}

function onOperandUpdate(
    operandIndex: number,
    updatedOperand: LiteralOperand,
): void {
    const operands = [...clause.operands];
    operands[operandIndex] = updatedOperand;
    syncSlider(operands);
    emit(UPDATE_CLAUSE_EVENT, { ...clause, operands });
}

function onDatePick(operandIndex: number, pickedValue: unknown): void {
    if (!(pickedValue instanceof Date)) {
        return;
    }
    onOperandUpdate(
        operandIndex,
        literalOperand(toLocalISODateString(pickedValue)),
    );
}
</script>

<template>
    <div class="time-operand-editor">
        <Select
            option-label="label"
            option-value="operator"
            :model-value="clause.operator"
            :options="operatorOptions"
            :placeholder="$gettext('Choose how to match dates')"
            :aria-label="$gettext('How to match dates')"
            @update:model-value="onOperatorChange"
        />

        <template v-if="valueCount > 0">
            <template v-if="isRange">
                <Message
                    v-if="boundsError"
                    severity="error"
                    size="small"
                >
                    {{ boundsError.message }}
                </Message>
                <TimeSlider
                    v-else-if="sliderBounds && sliderOffsets"
                    :model-value="sliderOffsets"
                    :bounds="sliderBounds"
                    @update:model-value="onSliderUpdate"
                />
                <span
                    v-else
                    class="time-operand-editor-hint"
                >
                    {{
                        $gettext(
                            "There are no dates to show on a timeline yet. Enter them below.",
                        )
                    }}
                </span>
            </template>

            <div
                v-for="(valueLabel, operandIndex) in valueLabels"
                :key="`${operandIndex}-${widgetRevision}`"
                class="time-operand-editor-value"
            >
                <span class="time-operand-editor-value-label">
                    {{ valueLabel }}
                </span>
                <ClauseOperandBuilder
                    v-if="subjectNode && subjectGraph"
                    :model-value="clause.operands[operandIndex] ?? null"
                    :subject-terminal-node="subjectNode"
                    :subject-terminal-graph="subjectGraph"
                    @update:model-value="onOperandUpdate(operandIndex, $event)"
                />
                <DatePicker
                    v-else-if="!isNodeSubject"
                    icon-display="input"
                    :model-value="storedDate(operandIndex)"
                    :show-icon="true"
                    :date-format="PICKER_DATE_FORMAT"
                    @update:model-value="onDatePick(operandIndex, $event)"
                />
            </div>
        </template>
    </div>
</template>

<style scoped>
.time-operand-editor {
    display: flex;
    flex-direction: column;
    gap: 1.6rem;
    padding: 1.6rem 2rem;
    font-size: 1.2rem;
}

.time-operand-editor :deep(.p-select-label) {
    font-size: 1.2rem;
}

.time-operand-editor .time-operand-editor-hint {
    color: var(--p-text-muted-color);
}

.time-operand-editor .time-operand-editor-value {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}

.time-operand-editor .time-operand-editor-value-label {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-weight: 600;
}
</style>
