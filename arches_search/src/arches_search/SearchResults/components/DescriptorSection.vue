<script setup lang="ts">
import { computed, inject } from "vue";
import { useGettext } from "vue3-gettext";

import Button from "primevue/button";
import Tag from "primevue/tag";

import arches from "arches";

import { generateArchesURL } from "@/arches_vue_components/application";

import type { Ref } from "vue";
import type { SectionContent } from "@/arches_modular_reports/ModularReport/types.ts";
import type { RelatedResource } from "@/arches_search/SimpleSearch/composables/useSidePanel.ts";
import type {
    ResourceDescriptorData,
    ResourceInstanceLifecycleState,
} from "@/arches_search/SearchResults/types.ts";

const { $gettext } = useGettext();

defineProps<{
    component: SectionContent;
}>();

const resourceInstanceId = inject("resourceInstanceId") as string;
const descriptorData = inject("descriptorData") as Ref<
    ResourceDescriptorData | null | undefined
>;
const lifecycleState = inject(
    "lifecycleState",
) as Ref<ResourceInstanceLifecycleState | null>;
const isExpanded = inject("searchResultExpanded") as Ref<boolean>;
const viewRelatedResource = inject("viewRelatedResource") as (
    resource: RelatedResource,
) => void;

function toggleExpanded(): void {
    isExpanded.value = !isExpanded.value;
}

function onViewRelated(): void {
    viewRelatedResource({
        id: resourceInstanceId,
        title: resourceDisplayName.value,
    });
}

const activeDescriptors = computed(function () {
    return descriptorData?.value?.descriptors?.[arches.activeLanguage];
});

const resourceDisplayName = computed<string>(function () {
    return activeDescriptors.value?.name || $gettext("Unnamed Resource");
});

const resourceDescriptionText = computed<string>(function () {
    return activeDescriptors.value?.description || "";
});

const resourceEditorLink = computed<string>(function () {
    return generateArchesURL("arches:resource_editor", {
        resourceid: resourceInstanceId,
    });
});

const resourceReportLink = computed<string>(function () {
    return generateArchesURL("arches:resource_report", {
        resourceid: resourceInstanceId,
    });
});

// Lifecycle states are admin-configurable, not a fixed enum, so severity is
// derived from the two permission flags every state always has, not name/id.
const lifecycleSeverity = computed<"warn" | "success" | "secondary">(() => {
    const state = lifecycleState?.value;
    if (!state) return "secondary";
    if (state.can_delete_resource_instances) return "warn";
    if (state.can_edit_resource_instances) return "success";
    return "secondary";
});
</script>

<template>
    <div class="descriptor-section">
        <div class="descriptor-section-content">
            <div class="descriptor-section-title-row">
                <a
                    :href="resourceReportLink"
                    target="_blank"
                    class="descriptor-section-title"
                >
                    {{ resourceDisplayName }}
                </a>
                <Tag
                    v-if="lifecycleState"
                    class="descriptor-section-lifecycle-tag"
                    :severity="lifecycleSeverity"
                    :value="lifecycleState.name"
                    rounded
                />
            </div>

            <div
                v-if="resourceDescriptionText"
                class="descriptor-section-description"
            >
                <span class="descriptor-section-description-label">
                    {{ $gettext("Description:") }}
                </span>
                {{ resourceDescriptionText }}
            </div>

            <div class="descriptor-section-actions">
                <Button
                    :icon="
                        isExpanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'
                    "
                    variant="link"
                    :label="
                        isExpanded
                            ? $gettext('Show less')
                            : $gettext('Show more')
                    "
                    @click="toggleExpanded"
                />
                <Button
                    as="a"
                    class="descriptor-section-view-report-action"
                    icon="pi pi-external-link"
                    target="_blank"
                    variant="link"
                    :href="resourceReportLink"
                    :label="$gettext('View Report')"
                />
                <Button
                    as="a"
                    icon="pi pi-wrench"
                    target="_blank"
                    variant="link"
                    :href="resourceEditorLink"
                    :label="$gettext('Edit')"
                />
                <Button
                    icon="pi pi-sitemap"
                    variant="link"
                    :label="$gettext('Related')"
                    @click="onViewRelated"
                />
            </div>
        </div>
    </div>
</template>

<style scoped>
.descriptor-section {
    display: flex;
    flex-direction: column;
}

.descriptor-section-content {
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
    flex: 1;
    min-width: 0;
    padding: 1.5rem 2rem;
}

.descriptor-section-title-row {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    flex-wrap: wrap;
}

.descriptor-section-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--p-primary-color);
    text-decoration: none;
    line-height: 1.3;
}

.descriptor-section-title:hover {
    text-decoration: underline;
}

.descriptor-section-lifecycle-tag.p-tag {
    font-size: 1rem;
    padding: 0.2rem 0.8rem;
    font-weight: 600;
    flex-shrink: 0;
}

.descriptor-section-actions {
    display: flex;
    align-items: center;
    gap: 0.2rem;
    margin-top: 0.2rem;
}

.descriptor-section-actions :deep(.p-button) {
    font-size: 1.2rem;
    padding: 0.3rem 0.8rem;
    color: var(--p-text-muted-color);
    text-decoration: none;
}

/* Aura's button.label.font.weight token sets an explicit weight on this
   span, which wins over the ancestor .p-button rule regardless of
   specificity — same as the toolbar-btn rules in ResultsToolbar.vue. */
.descriptor-section-actions :deep(.p-button-label) {
    font-weight: 600;
}

.descriptor-section-actions :deep(.p-button-icon) {
    font-size: 1.1rem;
}

.descriptor-section-actions
    :deep(.descriptor-section-view-report-action.p-button) {
    color: var(--p-primary-color);
}

.descriptor-section-actions
    :deep(.descriptor-section-view-report-action.p-button .p-button-label) {
    font-weight: 700;
}

.descriptor-section-description {
    font-size: 1.2rem;
    color: var(--p-text-muted-color);
    line-height: 1.4;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.descriptor-section-description-label {
    font-weight: 600;
    color: var(--p-text-muted-color);
    margin-inline-end: 0.4rem;
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 0.044rem;
}
</style>
