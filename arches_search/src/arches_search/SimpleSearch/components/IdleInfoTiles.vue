<script setup lang="ts">
import { useGettext } from "vue3-gettext";

const { $gettext } = useGettext();

defineProps<{
    hideFilters?: boolean;
    hideTime?: boolean;
}>();

defineEmits<{
    (event: "open-filters"): void;
    (event: "open-map"): void;
    (event: "open-time"): void;
    (event: "open-saved-searches"): void;
}>();
</script>

<template>
    <div class="idle-info-tiles">
        <div class="idle-info-tiles-header">
            {{ $gettext("Explore your results") }}
        </div>
        <div class="idle-info-tile-grid">
            <button
                v-if="!hideFilters"
                class="idle-info-tile"
                @click="$emit('open-filters')"
            >
                <i class="pi pi-filter idle-info-tile-icon" />
                <span class="idle-info-tile-title">
                    {{ $gettext("Facets") }}
                </span>
                <span class="idle-info-tile-desc">
                    {{
                        $gettext(
                            "Filter results by model-specific attributes and controlled values.",
                        )
                    }}
                </span>
            </button>
            <button
                class="idle-info-tile"
                @click="$emit('open-map')"
            >
                <i class="pi pi-map idle-info-tile-icon" />
                <span class="idle-info-tile-title">
                    {{ $gettext("Map View") }}
                </span>
                <span class="idle-info-tile-desc">
                    {{
                        $gettext(
                            "Plot results on an interactive map to explore spatial patterns.",
                        )
                    }}
                </span>
            </button>
            <button
                v-if="!hideTime"
                class="idle-info-tile"
                @click="$emit('open-time')"
            >
                <i class="pi pi-clock idle-info-tile-icon" />
                <span class="idle-info-tile-title">
                    {{ $gettext("Time Filters") }}
                </span>
                <span class="idle-info-tile-desc">
                    {{
                        $gettext(
                            "Narrow results to a date range using the timeline panel.",
                        )
                    }}
                </span>
            </button>
            <button
                class="idle-info-tile"
                @click="$emit('open-saved-searches')"
            >
                <i class="pi pi-bookmark idle-info-tile-icon" />
                <span class="idle-info-tile-title">
                    {{ $gettext("Save & Export") }}
                </span>
                <span class="idle-info-tile-desc">
                    {{
                        $gettext(
                            "Save this search for later or export the current results.",
                        )
                    }}
                </span>
            </button>
        </div>
    </div>
</template>

<style scoped>
.idle-info-tiles {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow-y: auto;
    background: var(--arches-search-card-bg);
}

.idle-info-tiles-header {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    padding: 1rem;
    min-height: 5.5rem;
    font-size: 1.2rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--p-text-muted-color);
    background: var(--arches-search-page-bg);
    border-block-end: 0.15rem solid var(--p-content-border-color);
}

.idle-info-tile-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.2rem;
    padding: 1.6rem;
}

.idle-info-tile {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 1.4rem 1.2rem;
    font-family: inherit;
    text-align: start;
    color: inherit;
    background: var(--arches-search-card-bg);
    border: 0.15rem solid var(--p-content-border-color);
    border-radius: 0.8rem;
    cursor: pointer;
    transition:
        border-color 0.12s,
        box-shadow 0.12s,
        background 0.12s;
}

.idle-info-tile:hover {
    background: var(--p-primary-50);
    border-color: var(--p-primary-color);
    box-shadow:
        0 0.4rem 1.2rem rgba(0, 0, 0, 0.09),
        0 0.2rem 0.4rem rgba(0, 0, 0, 0.05);
}

.idle-info-tile-icon {
    font-size: 2rem;
    color: var(--p-primary-color);
}

.idle-info-tile-title {
    font-size: 1.3rem;
    font-weight: 600;
    color: var(--p-text-color);
}

.idle-info-tile-desc {
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
    line-height: 1.4;
}
</style>
