import type { FeatureCollection } from "geojson";
import type { GroupPayload } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    DateRangeFilter,
    SearchRequestTerm,
} from "@/arches_search/SimpleSearch/types.ts";

export interface LandingTab {
    slug: string;
    label: string;
    icon: string;
    component: string;
}

export interface LandingBranding {
    eyebrow: string | null;
    title: string | null;
    subtitle: string | null;
    aboutIcon: string | null;
    aboutHeading: string | null;
    aboutBody: string[] | null;
}

export interface ResourceTypeCount {
    graphId: string;
    count: number;
}

export interface SearchDefinitionCountRequest {
    id: string;
    body: {
        terms: SearchRequestTerm[];
        query: GroupPayload | undefined;
        dateRange: DateRangeFilter | null;
        graphSlugs: string[];
        mapFilter: FeatureCollection | null;
    };
}
