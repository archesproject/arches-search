<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";
import Message from "openvue/message";
import Select from "openvue/select";
import SelectButton from "openvue/selectbutton";
import Tag from "openvue/tag";

import QueryAddButtons from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryAddButtons.vue";
import QueryItemList from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/QueryItemList.vue";

import { useQueryDescription } from "@/arches_search/AdvancedSearch/composables/useQueryDescription.ts";
import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";
import { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";

import type { Ref } from "vue";
import type {
    AdvancedSearchFacet,
    GraphModel,
} from "@/arches_search/AdvancedSearch/types.ts";

const SEARCH_EVENT = "search" as const;
const DESCRIBE_EVENT = "describe" as const;
const CLEAR_ALL_EVENT = "clear-all" as const;

const { isSearching } = defineProps<{
    isSearching: boolean;
}>();

const emit = defineEmits<{
    (event: typeof SEARCH_EVENT): void;
    (event: typeof DESCRIBE_EVENT): void;
    (event: typeof CLEAR_ALL_EVENT): void;
}>();

const graphs = inject<Ref<GraphModel[]>>("graphs")!;
const datatypesToAdvancedSearchFacets = inject<
    Ref<Record<string, AdvancedSearchFacet[]>>
>("datatypesToAdvancedSearchFacets")!;

const { $gettext, $pgettext } = useGettext();
const queryBuilder = useQueryBuilder();
const { root, prunedPayload, hasUnsearchedChanges } = queryBuilder;
const { description } = useQueryDescription({
    payload: prunedPayload,
    graphs,
    datatypesToAdvancedSearchFacets,
});

const pendingGraphSlug = ref<string | null>(null);

const hasConditions = computed<boolean>(
    () => (root.value?.items.length ?? 0) > 0,
);

const resourceModelOptions = computed(() =>
    graphs.value
        .filter((graph) => graph.isresource && graph.is_active)
        .map((graph) => ({ label: graph.name, value: graph.slug })),
);

const logicOptions = computed(() => [
    { label: $gettext("ALL"), value: LogicToken.AND },
    { label: $gettext("ANY"), value: LogicToken.OR },
]);

const inlineDescription = computed<string>(
    () =>
        description.value ||
        $gettext("Add conditions above to build your query…"),
);

const pendingGraphName = computed<string>(
    () =>
        resourceModelOptions.value.find(
            (option) => option.value === pendingGraphSlug.value,
        )?.label ?? "",
);

function onSelectGraph(graphSlug: string): void {
    if (root.value?.graphSlug === graphSlug) {
        return;
    }
    if (hasConditions.value) {
        pendingGraphSlug.value = graphSlug;
        return;
    }
    queryBuilder.startQuery(graphSlug);
}

function onConfirmGraphChange(): void {
    if (pendingGraphSlug.value) {
        queryBuilder.startQuery(pendingGraphSlug.value);
    }
    pendingGraphSlug.value = null;
}

function onCancelGraphChange(): void {
    pendingGraphSlug.value = null;
}

function onRootLogicChange(nextLogic: LogicToken | null): void {
    if (root.value && nextLogic && nextLogic !== root.value.logic) {
        queryBuilder.toggleGroupLogic(root.value.id);
    }
}
</script>

<template>
    <section class="query-builder">
        <div class="query-builder-sentence">
            <span class="query-builder-word">
                {{
                    $pgettext(
                        "Sentence: 'Find [resource model] where [ALL/ANY] of these conditions match:'",
                        "Find",
                    )
                }}
            </span>
            <Select
                class="query-builder-model-select"
                option-label="label"
                option-value="value"
                :model-value="root?.graphSlug ?? null"
                :options="resourceModelOptions"
                :filter="true"
                :placeholder="$gettext('Select a resource model')"
                :aria-label="$gettext('Resource model')"
                @update:model-value="onSelectGraph"
            />
            <template v-if="root">
                <span class="query-builder-word">
                    {{
                        $pgettext(
                            "Sentence: 'Find [resource model] where [ALL/ANY] of these conditions match:'",
                            "where",
                        )
                    }}
                </span>
                <SelectButton
                    option-label="label"
                    option-value="value"
                    :model-value="root.logic"
                    :options="logicOptions"
                    :allow-empty="false"
                    :aria-label="$gettext('Match all or any conditions')"
                    @update:model-value="onRootLogicChange"
                />
                <span class="query-builder-word">
                    {{
                        $pgettext(
                            "Sentence: 'Find [resource model] where [ALL/ANY] of these conditions match:'",
                            "of these conditions match:",
                        )
                    }}
                </span>
            </template>
        </div>

        <Message
            v-if="pendingGraphSlug"
            severity="warn"
            :closable="false"
        >
            <div class="query-builder-confirm">
                <span>
                    {{
                        $gettext(
                            "Changing to %{model} clears the current conditions.",
                            { model: pendingGraphName },
                        )
                    }}
                </span>
                <Button
                    size="small"
                    severity="warn"
                    :label="$gettext('Change model')"
                    @click="onConfirmGraphChange"
                />
                <Button
                    size="small"
                    severity="secondary"
                    variant="text"
                    :label="$gettext('Cancel')"
                    @click="onCancelGraphChange"
                />
            </div>
        </Message>

        <template v-if="root">
            <QueryItemList
                :container-id="root.id"
                :items="root.items"
                :logic="root.logic"
                :depth="0"
            />
            <QueryAddButtons :container-id="root.id" />
        </template>
        <span
            v-else
            class="query-builder-hint"
        >
            <i
                aria-hidden="true"
                class="pi pi-info-circle"
            />
            <span>
                {{
                    $gettext(
                        "Select a resource model above to start building your query.",
                    )
                }}
            </span>
        </span>

        <div class="query-builder-actions">
            <Button
                icon="pi pi-search"
                :label="$gettext('Search')"
                :loading="isSearching"
                :disabled="!root || isSearching"
                @click="emit(SEARCH_EVENT)"
            />
            <Tag
                v-if="hasUnsearchedChanges"
                severity="warn"
                :value="$gettext('Not yet searched')"
            />
            <Button
                icon="pi pi-comment"
                severity="secondary"
                variant="outlined"
                :label="$gettext('Describe Query')"
                :disabled="!prunedPayload"
                @click="emit(DESCRIBE_EVENT)"
            />
            <Button
                severity="secondary"
                variant="text"
                :label="$gettext('Clear all')"
                :disabled="!root"
                @click="emit(CLEAR_ALL_EVENT)"
            />
            <span
                class="query-builder-description"
                :class="{ 'query-builder-description-empty': !description }"
            >
                {{ inlineDescription }}
            </span>
        </div>
    </section>
</template>

<style scoped>
.query-builder {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    gap: 1.6rem;
    max-block-size: var(--arches-search-query-builder-max-height);
    overflow-y: auto;
    padding: 2rem 2.4rem 2.2rem;
    border-block-end: 0.2rem solid var(--arches-search-query-builder-border);
    background: var(--arches-search-query-builder-bg);
}

.query-builder .query-builder-sentence {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
}

.query-builder .query-builder-word {
    color: var(--arches-search-query-builder-word);
    font-size: 1.6rem;
    font-weight: 600;
    white-space: nowrap;
}

.query-builder .query-builder-model-select {
    min-inline-size: 22rem;
}

.query-builder .query-builder-confirm {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
}

.query-builder .query-builder-hint {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
}

.query-builder .query-builder-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
    padding-block-start: 1.6rem;
    border-block-start: 0.1rem solid var(--arches-search-query-builder-border);
}

.query-builder .query-builder-description {
    flex: 1;
    max-inline-size: 48rem;
    margin-inline-start: auto;
    color: var(--arches-search-query-builder-word);
    font-size: 1.2rem;
    font-style: italic;
    line-height: 1.5;
    text-align: end;
}

.query-builder .query-builder-description.query-builder-description-empty {
    color: var(--p-text-muted-color);
    font-style: normal;
}
</style>
