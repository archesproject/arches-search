import { useGettext } from "vue3-gettext";

import type {
    LandingBranding,
    LandingTab,
} from "@/arches_search/SearchLanding/types.ts";

export function useLandingContent(): {
    branding: LandingBranding;
    tabs: LandingTab[];
} {
    const { $gettext } = useGettext();

    return {
        branding: {
            eyebrow: $gettext("Search"),
            title: $gettext("Search the Collection"),
            subtitle: $gettext(
                "Find resources by keyword, resource type, location, or saved search.",
            ),
            aboutIcon: "pi pi-info",
            aboutHeading: $gettext("About this collection"),
            aboutBody: [
                $gettext(
                    "Use the search bar, browse by resource type, draw an area on the map, or revisit a saved search to get started.",
                ),
            ],
        },
        tabs: [
            {
                slug: "resource-types",
                label: $gettext("Resource Types"),
                icon: "pi pi-sitemap",
                component:
                    "arches_search/SearchLanding/components/ResourceTypesTab",
            },
            {
                slug: "map",
                label: $gettext("Map"),
                icon: "pi pi-map",
                component:
                    "arches_search/SearchLanding/components/MapTab/MapTab",
            },
            {
                slug: "saved-searches",
                label: $gettext("Saved Searches"),
                icon: "pi pi-bookmark-fill",
                component:
                    "arches_search/SearchLanding/components/SavedSearchesTab",
            },
        ],
    };
}
