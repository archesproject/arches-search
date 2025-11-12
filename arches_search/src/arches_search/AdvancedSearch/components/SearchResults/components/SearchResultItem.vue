<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";

import arches from "arches";

import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

import type { ResourceData } from "@/arches_search/AdvancedSearch/types.ts";

const { result } = defineProps<{
    result: ResourceData;
}>();
const { $gettext } = useGettext();
const thumbnailExists = ref(false);
const resourceLink = ref<string>();

onMounted(async () => {
    thumbnailExists.value = (
        await fetch(
            generateArchesURL("arches:thumbnail", {
                resource_id: result.resourceinstanceid,
            }),
            { method: "HEAD" },
        )
    ).ok;
    resourceLink.value = generateArchesURL("arches:resource_editor", {
        resourceid: result.resourceinstanceid,
    });
});
</script>
<template>
    <div class="search-result">
        <div class="thumbnail">
            <img
                v-if="thumbnailExists"
                :src="`/thumbnail/${result.resourceinstanceid}`"
            />
        </div>
        <div class="content">
            <h1>
                <a
                    target="_blank"
                    :href="resourceLink"
                    >{{ result.descriptors?.[arches.activeLanguage].name }}</a
                >
            </h1>
            <div class="description">
                {{ result.descriptors?.[arches.activeLanguage].description }}
            </div>
            <div class="actions">
                <div>
                    <Button
                        as="a"
                        icon="pi pi-chevron-right"
                        target="_blank"
                        size="large"
                        variant="link"
                        :label="$gettext('Show More')"
                        style="text-decoration: none"
                        @click.stop
                    />
                </div>

                <div>
                    <Button
                        as="a"
                        icon="pi pi-wrench"
                        target="_blank"
                        size="large"
                        variant="link"
                        :label="$gettext('Edit')"
                        style="text-decoration: none"
                        :href="resourceLink"
                        @click.stop
                    />
                </div>
            </div>
        </div>
    </div>
</template>
<style lang="css" scoped>
.search-result {
    display: flex;
    margin: 2rem;
}
.search-result h1 {
    font-size: 2rem;
    margin: 0;
}
.search-result h1 > a {
    color: steelblue;
}
.description {
    flex: 1;
}
.thumbnail {
    width: 10rem;
    height: 10rem;
    background-color: var(--p-surface-100);
    border-color: var(--p-surface-300);
    margin: 0;
}
.content {
    margin: 0 2rem;
    display: flex;
    flex-direction: column;
}
.content .actions {
    display: flex;
    align-items: center;
}
</style>
