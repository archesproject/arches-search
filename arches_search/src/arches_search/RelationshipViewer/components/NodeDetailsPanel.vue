<script setup lang="ts">
import Button from "primevue/button";
import type { GraphNode } from "@/arches_search/RelationshipViewer/types.ts";

const props = defineProps<{
    node: GraphNode | null;
}>();

const emit = defineEmits<{
    (e: "close"): void;
    (e: "expand-node", nodeId: string): void;
}>();

function openInArches() {
    if (!props.node) return;
    window.open(`/resource/${props.node.id}`, "_blank");
}
</script>

<template>
    <div
        v-if="props.node"
        class="node-details-panel"
    >
        <div class="panel-header">
            <div class="node-name">{{ props.node.name }}</div>
            <Button
                icon="pi pi-times"
                severity="secondary"
                size="small"
                text
                @click="emit('close')"
            />
        </div>

        <div class="meta-row">
            <span
                class="graph-badge"
                :style="{
                    background: props.node.graph_color ?? '#4e79a7',
                }"
            >
                <i
                    v-if="props.node.graph_icon"
                    :class="props.node.graph_icon"
                />
                {{ props.node.graph_name ?? props.node.graph_slug ?? "Unknown" }}
            </span>
            <span
                v-if="props.node.is_seed"
                class="seed-badge"
            >
                seed
            </span>
        </div>

        <div class="stat-row">
            <span>
                <strong>{{ props.node.related_count }}</strong> related
            </span>
        </div>

        <div
            v-if="props.node.attributes.length"
            class="attributes-section"
        >
            <div class="attr-title">Attributes</div>
            <dl>
                <template
                    v-for="attr in props.node.attributes"
                    :key="attr.alias"
                >
                    <dt>{{ attr.alias.replace(/_/g, " ") }}</dt>
                    <dd
                        v-for="(val, i) in attr.values"
                        :key="i"
                    >
                        {{ val }}
                    </dd>
                </template>
            </dl>
        </div>

        <div class="panel-actions">
            <Button
                size="small"
                severity="secondary"
                icon="pi pi-external-link"
                label="Open Record"
                @click="openInArches"
            />
            <Button
                size="small"
                severity="secondary"
                icon="pi pi-sitemap"
                label="Expand Here"
                @click="emit('expand-node', props.node!.id)"
            />
        </div>
    </div>
</template>

<style scoped>
.node-details-panel {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
    font-size: 13px;
    height: 100%;
    overflow-y: auto;
    background: #fff;
    border-left: 1px solid #ddd;
}
.panel-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
}
.node-name {
    font-weight: 600;
    font-size: 14px;
    color: #25476a;
    line-height: 1.3;
}
.meta-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
}
.graph-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 12px;
    color: #fff;
    font-size: 11px;
    font-weight: 600;
}
.seed-badge {
    background: #e8f0fa;
    color: #25476a;
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.stat-row {
    color: #666;
    font-size: 12px;
}
.attributes-section {
    flex: 1;
}
.attr-title {
    font-weight: 600;
    color: #25476a;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
}
dl {
    margin: 0;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 3px 10px;
}
dt {
    font-weight: 600;
    color: #555;
    font-size: 11px;
    text-transform: capitalize;
    white-space: nowrap;
    padding-top: 1px;
}
dd {
    margin: 0;
    color: #333;
    font-size: 12px;
    word-break: break-word;
}
.panel-actions {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    border-top: 1px solid #eee;
    padding-top: 8px;
}
</style>
