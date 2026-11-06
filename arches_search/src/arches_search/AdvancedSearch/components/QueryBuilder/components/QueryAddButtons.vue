<script setup lang="ts">
import { computed } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "openvue/button";

import { useQueryBuilder } from "@/arches_search/AdvancedSearch/composables/useQueryBuilder.ts";

const { containerId, isNested = false } = defineProps<{
    containerId: string;
    isNested?: boolean;
}>();

const { $gettext, $ngettext } = useGettext();
const queryBuilder = useQueryBuilder();
const { isSelecting, selectedItemIds, canGroupSelection } = queryBuilder;

const attributeLabel = computed<string>(() => {
    if (isNested) {
        return $gettext("Attribute");
    }
    return $gettext("Add attribute filter");
});

const relatedLabel = computed<string>(() => {
    if (isNested) {
        return $gettext("Related");
    }
    return $gettext("Add relationship filter");
});

const groupLabel = computed<string>(() => {
    if (isNested) {
        return $gettext("Sub-group");
    }
    return $gettext("Add group");
});

const groupSelectedLabel = computed<string>(() =>
    $ngettext(
        "Group %{count} selected",
        "Group %{count} selected",
        selectedItemIds.value.length,
        { count: String(selectedItemIds.value.length) },
    ),
);

function onAddAttribute(): void {
    queryBuilder.addRow(containerId);
}

function onAddRelated(): void {
    queryBuilder.addRelatedGroup(containerId);
}

function onAddGroup(): void {
    queryBuilder.addGroup(containerId);
}

function onStartSelecting(): void {
    queryBuilder.startSelecting();
}

function onStopSelecting(): void {
    queryBuilder.stopSelecting();
}

function onGroupSelected(): void {
    queryBuilder.groupSelectedItems();
}
</script>

<template>
    <div
        class="query-add-buttons"
        :class="{ 'query-add-buttons-nested': isNested }"
    >
        <span
            v-if="isNested"
            class="query-add-buttons-label"
        >
            {{ $gettext("Add:") }}
        </span>
        <Button
            icon="pi pi-plus"
            class="query-add-button"
            size="small"
            variant="outlined"
            severity="secondary"
            :label="attributeLabel"
            @click="onAddAttribute"
        />
        <Button
            icon="pi pi-plus"
            class="query-add-button"
            size="small"
            variant="outlined"
            severity="secondary"
            :label="relatedLabel"
            @click="onAddRelated"
        />
        <Button
            icon="pi pi-th-large"
            class="query-add-button"
            size="small"
            variant="outlined"
            severity="secondary"
            :label="groupLabel"
            @click="onAddGroup"
        />

        <template v-if="!isNested">
            <Button
                v-if="!isSelecting"
                class="query-add-buttons-selection"
                icon="pi pi-check-square"
                size="small"
                variant="outlined"
                severity="secondary"
                :label="$gettext('Select to group')"
                :title="
                    $gettext(
                        'Select conditions or groups and wrap them in a new group',
                    )
                "
                @click="onStartSelecting"
            />
            <template v-else>
                <Button
                    icon="pi pi-th-large"
                    class="query-add-buttons-selection"
                    size="small"
                    :label="groupSelectedLabel"
                    :disabled="!canGroupSelection"
                    @click="onGroupSelected"
                />
                <Button
                    class="query-add-buttons-selection"
                    size="small"
                    variant="outlined"
                    severity="secondary"
                    :label="$gettext('Cancel')"
                    @click="onStopSelecting"
                />
                <span class="query-add-buttons-hint">
                    {{
                        $gettext(
                            "Check two or more items at the same level, then click Group.",
                        )
                    }}
                </span>
            </template>
        </template>
    </div>
</template>

<style scoped>
.query-add-buttons {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.8rem;
}

.query-add-buttons.query-add-buttons-nested {
    padding-block-start: 0.8rem;
    border-block-start: 0.1rem dashed var(--p-content-border-color);
}

.query-add-buttons .query-add-buttons-label {
    color: var(--p-text-muted-color);
    font-size: 1.2rem;
    font-weight: 600;
}

.query-add-buttons .query-add-button {
    border-style: dashed;
    font-size: 1.2rem;
}

.query-add-buttons .query-add-buttons-selection {
    font-size: 1.2rem;
}

.query-add-buttons .query-add-buttons-hint {
    color: var(--p-text-muted-color);
    font-size: 1.1rem;
    font-style: italic;
}
</style>
