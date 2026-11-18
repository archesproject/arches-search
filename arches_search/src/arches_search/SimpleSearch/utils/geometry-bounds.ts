import type { Geometry, Position } from "geojson";

type LngLatBoundsTuple = [[number, number], [number, number]];

export function boundsOfGeometries(
    geometries: Geometry[],
): LngLatBoundsTuple | null {
    let west = Infinity;
    let south = Infinity;
    let east = -Infinity;
    let north = -Infinity;

    for (const geometry of geometries) {
        for (const [longitude, latitude] of positionsOfGeometry(geometry)) {
            west = Math.min(west, longitude);
            south = Math.min(south, latitude);
            east = Math.max(east, longitude);
            north = Math.max(north, latitude);
        }
    }

    if (west === Infinity) {
        return null;
    }
    return [
        [west, south],
        [east, north],
    ];
}

function positionsOfGeometry(geometry: Geometry): Position[] {
    switch (geometry.type) {
        case "Point":
            return [geometry.coordinates];
        case "MultiPoint":
        case "LineString":
            return geometry.coordinates;
        case "MultiLineString":
        case "Polygon":
            return geometry.coordinates.flat();
        case "MultiPolygon":
            return geometry.coordinates.flat(2);
        case "GeometryCollection":
            return geometry.geometries.flatMap(positionsOfGeometry);
    }
}
