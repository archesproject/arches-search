<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import RelationshipSentence from "@/arches_search/RelationshipGraph/components/RelationshipSentence.vue";

const { sourceName, targetName, relationshipTypeLabel, inverseLabel, notes } =
    defineProps<{
        sourceName: string;
        targetName: string;
        relationshipTypeLabel: string;
        inverseLabel: string;
        notes: string;
    }>();

const { $gettext } = useGettext();
</script>

<template>
    <div class="edge-details-popup">
        <h4 class="title">{{ $gettext("Relationship") }}</h4>

        <dl class="sides">
            <div class="side">
                <dt class="side-name">{{ $gettext("Forward") }}</dt>
                <dd class="side-value">
                    <RelationshipSentence
                        :from-name="sourceName"
                        :to-name="targetName"
                        :label="relationshipTypeLabel"
                    />
                </dd>
            </div>
            <div class="side">
                <dt class="side-name">{{ $gettext("Inverse") }}</dt>
                <dd class="side-value">
                    <RelationshipSentence
                        v-if="inverseLabel"
                        :from-name="targetName"
                        :to-name="sourceName"
                        :label="inverseLabel"
                    />
                    <span
                        v-else
                        class="not-recorded"
                    >
                        {{ $gettext("Not recorded") }}
                    </span>
                </dd>
            </div>
        </dl>

        <div
            v-if="notes"
            class="notes"
        >
            <span class="notes-label">{{ $gettext("Notes") }}</span>
            <p class="notes-text">{{ notes }}</p>
        </div>
    </div>
</template>

<style scoped>
.edge-details-popup {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.edge-details-popup .title {
    margin: 0;
    /* Clear of the close button */
    padding-inline-end: 3rem;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--p-text-color);
}

.edge-details-popup .sides {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    margin: 0;
}

.edge-details-popup .sides .side {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.edge-details-popup .sides .side .side-name,
.edge-details-popup .notes .notes-label {
    font-size: 1.1rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--p-text-muted-color);
}

.edge-details-popup .sides .side .side-value {
    margin: 0;
    font-size: 1.3rem;
    color: var(--p-text-color);
}

.edge-details-popup .sides .side .side-value .not-recorded {
    color: var(--p-text-muted-color);
}

.edge-details-popup .notes {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.edge-details-popup .notes .notes-text {
    margin: 0;
    font-size: 1.3rem;
    color: var(--p-text-color);
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}
</style>
