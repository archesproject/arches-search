<script setup lang="ts">
import {
    defineProps,
    defineEmits,
    inject,
    ref,
    computed,
    watch,
    defineOptions,
} from "vue";
import { useGettext } from "vue3-gettext";
import Select from "primevue/select";
import Button from "primevue/button";
import Card from "primevue/card";
import Divider from "primevue/divider";

import {
    GraphScopeToken,
    LogicToken,
    makeEmptyGroupPayload,
    makeEmptyLiteralClause,
    makeEmptyRelationshipBlock,
    type GroupPayload,
} from "@/arches_search/AdvancedSearch/advanced-search-payload-builder.ts";

defineOptions({ name: "GroupPayloadBuilder" });

const { $gettext } = useGettext();

type GraphSummary =
    | { id?: string; slug: string; name?: string; label?: string }
    | Record<string, unknown>;

const graphs = inject<Readonly<{ value: GraphSummary[] }>>("graphs");

const emit = defineEmits<{
    (event: "update:modelValue", value: GroupPayload): void;
    (event: "remove"): void;
}>();

const props = defineProps<{
    modelValue?: GroupPayload;
    isRoot?: boolean;
}>();

const currentGroup = computed<GroupPayload>(
    () => props.modelValue ?? makeEmptyGroupPayload(),
);

const childGroupKeys = ref<string[]>([]);
const clauseKeys = ref<string[]>([]);

function createId(): string {
    return globalThis.crypto.randomUUID();
}

if (currentGroup.value) {
    childGroupKeys.value = Array.from(
        { length: currentGroup.value.groups.length },
        () => createId(),
    );
    clauseKeys.value = Array.from(
        { length: currentGroup.value.clauses.length },
        () => createId(),
    );
}

watch(
    () => currentGroup.value?.groups.length ?? 0,
    (newLength, oldLength) => {
        if (newLength > oldLength) {
            for (let index = 0; index < newLength - oldLength; index += 1) {
                childGroupKeys.value.push(createId());
            }
        } else if (newLength < oldLength) {
            childGroupKeys.value.splice(newLength);
        }
    },
);

watch(
    () => currentGroup.value?.clauses.length ?? 0,
    (newLength, oldLength) => {
        if (newLength > oldLength) {
            for (let index = 0; index < newLength - oldLength; index += 1) {
                clauseKeys.value.push(createId());
            }
        } else if (newLength < oldLength) {
            clauseKeys.value.splice(newLength);
        }
    },
);

function updateGroup(nextGroup: GroupPayload): void {
    emit("update:modelValue", nextGroup);
}

function setGraphSlug(graphSlug: string): void {
    updateGroup({ ...currentGroup.value, graph_slug: graphSlug });
}

function setScope(scopeToken: GraphScopeToken): void {
    updateGroup({ ...currentGroup.value, scope: scopeToken });
}

const logicLabel = computed(() =>
    currentGroup.value.logic === LogicToken.AND
        ? $gettext("AND")
        : $gettext("OR"),
);
const isAnd = computed(() => currentGroup.value.logic === LogicToken.AND);

function toggleLogic(): void {
    const nextLogic = isAnd.value ? LogicToken.OR : LogicToken.AND;
    updateGroup({ ...currentGroup.value, logic: nextLogic });
}

function addGroup(): void {
    const childGroup: GroupPayload = {
        ...makeEmptyGroupPayload(),
        graph_slug: currentGroup.value.graph_slug,
        scope: currentGroup.value.scope,
    };
    updateGroup({
        ...currentGroup.value,
        groups: [...currentGroup.value.groups, childGroup],
    });
}

function replaceChildGroup(
    childIndex: number,
    replacement: GroupPayload,
): void {
    const nextGroups = currentGroup.value.groups.slice();
    nextGroups.splice(childIndex, 1, replacement);
    updateGroup({ ...currentGroup.value, groups: nextGroups });
}

function removeGroupAtIndex(childIndex: number): void {
    const nextGroups = currentGroup.value.groups.slice();
    nextGroups.splice(childIndex, 1);
    updateGroup({ ...currentGroup.value, groups: nextGroups });
}

function addClause(): void {
    const nextClauses = currentGroup.value.clauses.slice();
    nextClauses.push(makeEmptyLiteralClause());
    updateGroup({ ...currentGroup.value, clauses: nextClauses });
}

function removeClauseAtIndex(clauseIndex: number): void {
    const nextClauses = currentGroup.value.clauses.slice();
    nextClauses.splice(clauseIndex, 1);
    updateGroup({ ...currentGroup.value, clauses: nextClauses });
}

function addRelationship(): void {
    if (currentGroup.value.relationship !== null) return;
    updateGroup({
        ...currentGroup.value,
        relationship: makeEmptyRelationshipBlock(),
    });
}

function removeRelationship(): void {
    if (currentGroup.value.relationship === null) return;
    updateGroup({ ...currentGroup.value, relationship: null });
}

const scopeOptions = computed(() => [
    { label: $gettext("Resource"), value: GraphScopeToken.RESOURCE },
    { label: $gettext("Tile"), value: GraphScopeToken.TILE },
]);

const graphOptions = computed(() => {
    const graphList = graphs?.value ?? [];
    return graphList
        .map((graphEntry: GraphSummary) => {
            const slug = (graphEntry as { slug?: string }).slug ?? "";
            const displayName =
                (graphEntry as { name?: string }).name ??
                (graphEntry as { label?: string }).label ??
                slug;
            return { label: String(displayName), value: String(slug) };
        })
        .filter((option) => option.value.length > 0);
});

const itemCount = computed(
    () => currentGroup.value.groups.length + currentGroup.value.clauses.length,
);
const showBracket = computed(() => itemCount.value >= 2);
</script>

<template>
    <div
        class="group-wrap"
        :class="{ 'is-root': isRoot }"
        :style="isRoot ? { gridTemplateColumns: '1fr' } : undefined"
    >
        <template v-if="!isRoot">
            <div
                v-if="showBracket"
                :class="['bracket-col', isAnd ? 'is-and' : 'is-or']"
            >
                <div class="spine spine--top"></div>
                <div class="logic-lane">
                    <Button
                        :label="logicLabel"
                        class="logic-button"
                        size="small"
                        @click="toggleLogic"
                    />
                </div>
                <div class="spine spine--bottom"></div>
                <div class="arm arm--top"></div>
                <div class="arm arm--bottom"></div>
            </div>
            <div
                v-else
                class="bracket-spacer"
            ></div>
        </template>

        <Card class="group-card">
            <template #title>
                <div class="group-header">
                    <div class="row">
                        <Select
                            :model-value="currentGroup.graph_slug"
                            :options="graphOptions"
                            option-label="label"
                            option-value="value"
                            :placeholder="$gettext('Select graph')"
                            class="field"
                            @update:model-value="setGraphSlug"
                        />
                        <Select
                            :model-value="currentGroup.scope"
                            :options="scopeOptions"
                            option-label="label"
                            option-value="value"
                            class="field"
                            @update:model-value="setScope"
                        />
                    </div>

                    <div class="actions">
                        <Button
                            severity="secondary"
                            icon="pi pi-plus"
                            :label="$gettext('Add group')"
                            @click="addGroup"
                        />
                        <Button
                            severity="secondary"
                            icon="pi pi-plus"
                            :label="$gettext('Add clause')"
                            @click="addClause"
                        />
                        <Button
                            v-if="currentGroup.relationship === null"
                            severity="secondary"
                            icon="pi pi-link"
                            :label="$gettext('Add relationship')"
                            @click="addRelationship"
                        />
                        <Button
                            v-else
                            severity="danger"
                            icon="pi pi-unlink"
                            :label="$gettext('Remove relationship')"
                            @click="removeRelationship"
                        />
                        <Button
                            v-if="!isRoot"
                            severity="danger"
                            icon="pi pi-times"
                            :label="$gettext('Remove group')"
                            @click="$emit('remove')"
                        />
                    </div>
                </div>
            </template>

            <template #content>
                <div
                    class="content-grid"
                    :class="{ 'with-root-bracket': isRoot && showBracket }"
                >
                    <div
                        v-if="isRoot && showBracket"
                        :class="['bracket-col', isAnd ? 'is-and' : 'is-or']"
                    >
                        <div class="spine spine--top"></div>
                        <div class="logic-lane">
                            <Button
                                :label="logicLabel"
                                class="logic-button"
                                size="small"
                                @click="toggleLogic"
                            />
                        </div>
                        <div class="spine spine--bottom"></div>
                        <div class="arm arm--top"></div>
                        <div class="arm arm--bottom"></div>
                    </div>

                    <div
                        class="body"
                        :style="
                            isRoot && showBracket
                                ? { gridColumn: '2' }
                                : { gridColumn: '1 / -1' }
                        "
                    >
                        <div
                            v-if="currentGroup.clauses.length > 0"
                            class="clauses"
                        >
                            <div
                                v-for="(
                                    _clausePayload, clauseIndex
                                ) in currentGroup.clauses"
                                :key="clauseKeys[clauseIndex]"
                                class="clause-row"
                            >
                                <span
                                    >{{ $gettext("Clause") }}
                                    {{ clauseIndex + 1 }}</span
                                >
                                <Button
                                    severity="danger"
                                    icon="pi pi-trash"
                                    :label="$gettext('Remove clause')"
                                    @click="removeClauseAtIndex(clauseIndex)"
                                />
                            </div>
                            <Divider />
                        </div>

                        <div
                            v-if="currentGroup.groups.length > 0"
                            class="children"
                        >
                            <GroupPayloadBuilder
                                v-for="(
                                    childGroupPayload, childIndex
                                ) in currentGroup.groups"
                                :key="childGroupKeys[childIndex]"
                                :model-value="currentGroup.groups[childIndex]"
                                @update:model-value="
                                    (value) =>
                                        replaceChildGroup(childIndex, value)
                                "
                                @remove="removeGroupAtIndex(childIndex)"
                            />
                        </div>
                    </div>
                </div>
            </template>
        </Card>
    </div>
</template>

<style scoped>
.group-wrap {
    display: grid;
    grid-template-columns: 4rem 1fr;
    gap: 0;
    align-items: stretch;
    margin-bottom: 1rem;
}

.bracket-col {
    --spine-width: 0.3rem;
    --arm-length: 1.75rem;
    --arm-thickness: 0.3rem;
    display: grid;
    grid-template-columns: var(--spine-width) var(--arm-length);
    grid-template-rows: 1fr auto 1fr;
    align-items: center;
    justify-items: start;
    padding-inline-start: 0.5rem;
    row-gap: 0.75rem;
}

.bracket-col.is-and {
    --logic-color: var(--p-blue-600);
    --logic-hover-color: var(--p-blue-700);
}

.bracket-col.is-or {
    --logic-color: var(--p-orange-600);
    --logic-hover-color: var(--p-orange-700);
}

.bracket-spacer {
}

.spine {
    width: var(--spine-width);
    background: var(--logic-color);
    grid-column: 1;
    margin-inline-start: 0.75rem;
}
.spine--top {
    grid-row: 1;
    align-self: stretch;
}
.spine--bottom {
    grid-row: 3;
    align-self: stretch;
}

.logic-lane {
    grid-column: 1;
    grid-row: 2;
    display: grid;
    place-items: center;
    width: var(--spine-width);
}

.arm {
    background: var(--logic-color);
    height: var(--arm-thickness);
    grid-column: 2;
    width: 100%;
    margin-inline-start: 0.75rem;
}
.arm--top {
    grid-row: 1;
    align-self: start;
}
.arm--bottom {
    grid-row: 3;
    align-self: end;
}

.logic-button.p-button {
    background: var(--logic-color);
    border-color: var(--logic-color);
    color: var(--p-surface-0);
    padding-block: 0.25rem;
    padding-inline: 0.75rem;
    box-shadow: none;
}
.logic-button.p-button:enabled:hover {
    background: var(--logic-hover-color);
    border-color: var(--logic-hover-color);
    color: var(--p-surface-0);
}

.group-card {
    border: 0.0625rem solid var(--p-content-border-color);
    background: var(--p-content-background);
    box-shadow: none;
}

.group-header {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0.75rem;
    align-items: center;
}

.row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
}

.actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}

.content-grid {
    display: block;
}
.content-grid.with-root-bracket {
    display: grid;
    grid-template-columns: 4rem 1fr;
    gap: 0;
    align-items: stretch;
}

.body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.field {
    min-width: 12rem;
}

.clauses {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.clause-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0.5rem;
    align-items: center;
}

.children {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}
</style>
