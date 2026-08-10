import { generateArchesURL } from "@/arches_vue_components/application";

import arches from "arches";

import type {
    ResourceDescriptorData,
    ResourceInstanceLifecycleState,
    SearchReportConfig,
} from "@/arches_search/SearchResults/types.ts";

export async function fetchResourceDescriptors(
    ids: string[],
): Promise<Record<string, ResourceDescriptorData>> {
    if (ids.length === 0) {
        return {};
    }

    const params = new URLSearchParams();
    for (const id of ids) {
        params.append("ids", id);
    }

    const url =
        generateArchesURL("arches_search:api_resource_descriptors") +
        "?" +
        params.toString();

    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
}

// The full set of lifecycle-state definitions is bounded by admin
// configuration, not by how many resources exist, so this is fetched once
// and joined against resources client-side rather than resolved per-result
// server-side.
export async function fetchResourceInstanceLifecycleStates(): Promise<
    ResourceInstanceLifecycleState[]
> {
    const url = generateArchesURL(
        "arches:api_resource_instance_lifecycle_states",
    );
    const response = await fetch(url);
    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
}

export async function fetchSearchReportConfig(
    resourceId: string,
    slug: string = "search",
): Promise<SearchReportConfig | null> {
    const params = new URLSearchParams({
        resourceId,
        report_config_slug: slug,
    });

    const url = `${arches.urls.modular_report_config}?${params.toString()}`;

    const response = await fetch(url);

    if (response.status === 404) {
        return null;
    }

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);
    return parsed;
}
