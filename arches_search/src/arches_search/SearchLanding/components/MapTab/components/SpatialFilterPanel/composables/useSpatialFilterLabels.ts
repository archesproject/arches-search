import { computed } from "vue";

import { useGettext } from "vue3-gettext";

import type { ComputedRef, ShallowRef } from "vue";
import type { Feature } from "geojson";

export function useSpatialFilterLabels(
    drawnFeatures: ShallowRef<Feature[]>,
): ComputedRef<Record<string, string>> {
    const { $gettext } = useGettext();

    function getFeatureLabel(geometryType: string, count: number): string {
        const parameters = { count: String(count) };

        switch (geometryType) {
            case "Point":
                return $gettext("Point #%{count}", parameters);
            case "LineString":
                return $gettext("Line #%{count}", parameters);
            case "Polygon":
                return $gettext("Polygon #%{count}", parameters);
            default:
                return $gettext("Feature #%{count}", parameters);
        }
    }

    return computed(() => {
        const countByType: Record<string, number> = {};

        return Object.fromEntries(
            drawnFeatures.value.map((feature) => {
                const geometryType = feature.geometry.type;
                countByType[geometryType] =
                    (countByType[geometryType] ?? 0) + 1;

                return [
                    String(feature.id),
                    getFeatureLabel(geometryType, countByType[geometryType]),
                ];
            }),
        );
    });
}
