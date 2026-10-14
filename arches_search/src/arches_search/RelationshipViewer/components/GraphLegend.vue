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
                :class="{
                    hidden: group.hidden,
                    highlighted: group.highlighted,
                }"
            >
                <span
                    class="swatch"
                    :style="{ background: group.color }"
                />
                <span class="label">{{
                    group.name ?? group.slug ?? "Unknown"
                }}</span>
                <span class="count">{{ group.count }}</span>
                <button
                    class="action-btn"
                    :class="{ active: group.highlighted }"
                    :title="
                        group.highlighted
                            ? 'Clear highlight'
                            : 'Highlight all nodes of this type'
                    "
                    @click="emit('highlight', group.slug)"
                >
                    <i class="pi pi-star" />
                </button>
                <button
                    class="action-btn"
                    :title="
                        group.hidden ? 'Add back to graph' : 'Remove from graph'
                    "
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
    border: 0.1rem solid #aebdcb;
    border-radius: 0.6rem;
    padding: 0.8rem 1rem;
    min-width: 19rem;
    font-size: 1.2rem;
    box-shadow: 0 0.4rem 1.4rem rgba(17, 24, 39, 0.16);
    backdrop-filter: blur(0.2rem);
}
.legend-title {
    font-weight: 700;
    color: #13293d;
    margin-bottom: 0.6rem;
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 0.1rem solid #d5dee7;
    padding-bottom: 0.5rem;
}
ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}
li {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.3rem 0.4rem;
    border-radius: 0.3rem;
    transition: background 0.15s;
    color: #16202a;
    border-left: 0.2rem solid transparent;
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
    width: 1.3rem;
    height: 1.3rem;
    border-radius: 50%;
    flex-shrink: 0;
    border: 0.15rem solid rgba(0, 0, 0, 0.15);
}
.label {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 10rem;
    font-weight: 600;
    color: #2d3f52;
}
.count {
    color: #2d3f52;
    font-size: 1.1rem;
    font-weight: 600;
    min-width: 1.8rem;
    text-align: right;
}
.action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    padding: 0;
    border: none;
    border-radius: 0.3rem;
    background: transparent;
    color: #8fa3b8;
    cursor: pointer;
    flex-shrink: 0;
    transition:
        color 0.12s,
        background 0.12s;
    font-size: 1rem;
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
