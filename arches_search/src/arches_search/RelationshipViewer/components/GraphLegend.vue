<script setup lang="ts">
import type { GraphTypeGroup } from "@/arches_search/RelationshipViewer/types.ts";

const props = defineProps<{
    groups: GraphTypeGroup[];
}>();

const emit = defineEmits<{
    (e: "toggle", slug: string | null): void;
    (e: "highlight", slug: string | null): void;
}>();
</script>

<template>
    <div class="graph-legend">
        <div class="legend-title">Resource Types</div>
        <ul>
            <li
                v-for="group in props.groups"
                :key="String(group.slug)"
                :class="{ hidden: group.hidden, highlighted: group.highlighted }"
            >
                <span
                    class="swatch"
                    :style="{ background: group.color }"
                />
                <span class="label">{{ group.name ?? group.slug ?? "Unknown" }}</span>
                <span class="count">{{ group.count }}</span>
                <button
                    class="action-btn"
                    :class="{ active: group.highlighted }"
                    :title="group.highlighted ? 'Clear highlight' : 'Highlight all nodes of this type'"
                    @click="emit('highlight', group.slug)"
                >
                    <i class="pi pi-star" />
                </button>
                <button
                    class="action-btn"
                    :title="group.hidden ? 'Add back to graph' : 'Remove from graph'"
                    @click="emit('toggle', group.slug)"
                >
                    <i :class="group.hidden ? 'pi pi-plus' : 'pi pi-minus'" />
                </button>
            </li>
        </ul>
    </div>
</template>

<style scoped>
.graph-legend {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid #aebdcb;
    border-radius: 6px;
    padding: 8px 10px;
    min-width: 190px;
    font-size: 12px;
    box-shadow: 0 4px 14px rgba(17, 24, 39, 0.16);
    backdrop-filter: blur(2px);
}
.legend-title {
    font-weight: 700;
    color: #13293d;
    margin-bottom: 6px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #d5dee7;
    padding-bottom: 5px;
}
ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
}
li {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 4px;
    border-radius: 3px;
    transition: background 0.15s;
    color: #16202a;
    border-left: 2px solid transparent;
}
li:hover {
    background: #dde9f5;
}
li.hidden {
    border-left-color: transparent;
}
li.hidden .swatch {
    opacity: 0.35;
    filter: grayscale(80%);
}
li.hidden .label {
    color: #aab8c5;
    text-decoration: line-through;
    text-decoration-color: #aab8c5;
}
li.hidden .count {
    color: #aab8c5;
}
li.highlighted {
    border-left-color: #edc948;
    background: rgba(237, 201, 72, 0.08);
}
.swatch {
    width: 13px;
    height: 13px;
    border-radius: 50%;
    flex-shrink: 0;
    border: 1.5px solid rgba(0, 0, 0, 0.15);
}
.label {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100px;
    font-weight: 600;
    color: #2d3f52;
}
.count {
    color: #2d3f52;
    font-size: 11px;
    font-weight: 600;
    min-width: 18px;
    text-align: right;
}
.action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    padding: 0;
    border: none;
    border-radius: 3px;
    background: transparent;
    color: #8fa3b8;
    cursor: pointer;
    flex-shrink: 0;
    transition: color 0.12s, background 0.12s;
    font-size: 10px;
    line-height: 1;
}
.action-btn:hover {
    background: #c6d8ea;
    color: #25476a;
}
.action-btn.active {
    color: #c8a000;
}
.action-btn.active:hover {
    color: #9a7a00;
}
</style>
