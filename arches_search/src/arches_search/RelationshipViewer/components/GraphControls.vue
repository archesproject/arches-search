<script setup lang="ts">
import Button from "primevue/button";
import type { RelationshipType } from "@/arches_search/RelationshipViewer/types.ts";

const props = defineProps<{
    depth: 1 | 2;
    relationshipTypes: RelationshipType[];
    enabledRelTypeIds: Set<string>;
    pathfindMode: boolean;
    loading: boolean;
    nodeCount: number;
    edgeCount: number;
}>();

const emit = defineEmits<{
    (e: "update:depth", value: 1 | 2): void;
    (e: "update:enabledRelTypeIds", value: Set<string>): void;
    (e: "toggle-pathfind"): void;
    (e: "recenter"): void;
    (e: "reload"): void;
}>();

function toggleRelType(id: string) {
    const next = new Set(props.enabledRelTypeIds);
    if (next.has(id)) {
        next.delete(id);
    } else {
        next.add(id);
    }
    emit("update:enabledRelTypeIds", next);
}

function allEnabled() {
    return props.enabledRelTypeIds.size === 0;
}

function toggleAll() {
    emit("update:enabledRelTypeIds", new Set());
}
</script>

<template>
    <div class="graph-controls">
        <div class="controls-section">
            <div class="section-label">Expansion Depth</div>
            <div class="depth-buttons">
                <button
                    :class="{ active: props.depth === 1 }"
                    @click="emit('update:depth', 1)"
                >
                    1 hop
                </button>
                <button
                    :class="{ active: props.depth === 2 }"
                    @click="emit('update:depth', 2)"
                >
                    2 hops
                </button>
            </div>
        </div>

        <div class="controls-section">
            <div class="section-label">Graph</div>
            <div class="stat-row">
                <span>{{ props.nodeCount }} nodes</span>
                <span>{{ props.edgeCount }} edges</span>
            </div>
            <div class="button-row">
                <Button
                    size="small"
                    severity="secondary"
                    icon="pi pi-refresh"
                    label="Reload"
                    :loading="props.loading"
                    @click="emit('reload')"
                />
                <Button
                    size="small"
                    severity="secondary"
                    icon="pi pi-arrows-alt"
                    label="Recenter"
                    @click="emit('recenter')"
                />
            </div>
        </div>

        <div
            v-if="props.relationshipTypes.length"
            class="controls-section"
        >
            <div class="section-label">Relationship Types</div>
            <div class="rel-type-list">
                <label class="rel-type-item all-toggle">
                    <input
                        type="checkbox"
                        :checked="allEnabled()"
                        @change="toggleAll"
                    />
                    <span>All types</span>
                </label>
                <label
                    v-for="rt in props.relationshipTypes"
                    :key="rt.id"
                    class="rel-type-item"
                >
                    <input
                        type="checkbox"
                        :checked="
                            props.enabledRelTypeIds.size === 0 ||
                            props.enabledRelTypeIds.has(rt.id)
                        "
                        @change="toggleRelType(rt.id)"
                    />
                    <span class="rt-label">{{ rt.label }}</span>
                    <span class="rt-count">{{ rt.count }}</span>
                </label>
            </div>
        </div>

        <div class="controls-section">
            <div class="section-label">Path Finding</div>
            <Button
                size="small"
                :severity="props.pathfindMode ? 'danger' : 'secondary'"
                :icon="
                    props.pathfindMode ? 'pi pi-times' : 'pi pi-share-alt'
                "
                :label="
                    props.pathfindMode ? 'Cancel Path Find' : 'Find Path'
                "
                @click="emit('toggle-pathfind')"
            />
            <p
                v-if="props.pathfindMode"
                class="pathfind-hint"
            >
                Click a start node, then an end node.
            </p>
        </div>
    </div>
</template>

<style scoped>
.graph-controls {
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding: 12px;
    font-size: 12px;
    overflow-y: auto;
    height: 100%;
}
.controls-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.section-label {
    font-weight: 600;
    color: #25476a;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.depth-buttons {
    display: flex;
    gap: 4px;
}
.depth-buttons button {
    flex: 1;
    padding: 4px 8px;
    border: 1px solid #ccc;
    border-radius: 3px;
    background: #fff;
    cursor: pointer;
    font-size: 12px;
}
.depth-buttons button.active {
    background: #25476a;
    color: #fff;
    border-color: #25476a;
}
.stat-row {
    display: flex;
    gap: 10px;
    color: #666;
}
.button-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}
.rel-type-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-height: 200px;
    overflow-y: auto;
}
.rel-type-item {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    padding: 2px 0;
}
.rel-type-item.all-toggle {
    font-weight: 600;
    border-bottom: 1px solid #eee;
    padding-bottom: 4px;
    margin-bottom: 2px;
}
.rt-label {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.rt-count {
    color: #999;
    font-size: 10px;
}
.pathfind-hint {
    color: #666;
    font-size: 11px;
    margin: 0;
    font-style: italic;
}
</style>
