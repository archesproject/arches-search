<script setup lang="ts">
import Button from "openvue/button";
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
                {{
                    props.node.graph_name ?? props.node.graph_slug ?? "Unknown"
                }}
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
    gap: 1rem;
    padding: 1.2rem;
    font-size: 1.3rem;
    height: 100%;
    overflow-y: auto;
    background: #fff;
    border-left: 0.1rem solid #ddd;
}
.panel-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.8rem;
}
.node-name {
    font-weight: 600;
    font-size: 1.4rem;
    color: #25476a;
    line-height: 1.3;
}
.meta-row {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    align-items: center;
}
.graph-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.2rem 0.8rem;
    border-radius: 1.2rem;
    color: #fff;
    font-size: 1.1rem;
    font-weight: 600;
}
.seed-badge {
    background: #e8f0fa;
    color: #25476a;
    font-size: 1rem;
    padding: 0.1rem 0.6rem;
    border-radius: 1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.stat-row {
    color: #666;
    font-size: 1.2rem;
}
.attributes-section {
    flex: 1;
}
.attr-title {
    font-weight: 600;
    color: #25476a;
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.6rem;
}
dl {
    margin: 0;
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.3rem 1rem;
}
dt {
    font-weight: 600;
    color: #555;
    font-size: 1.1rem;
    text-transform: capitalize;
    white-space: nowrap;
    padding-top: 0.1rem;
}
dd {
    margin: 0;
    color: #333;
    font-size: 1.2rem;
    word-break: break-word;
}
.panel-actions {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    border-top: 0.1rem solid #eee;
    padding-top: 0.8rem;
}
</style>
