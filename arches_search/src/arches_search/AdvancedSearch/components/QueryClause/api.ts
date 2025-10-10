import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

export async function getFacetsByDatatype(datatype: string) {
    const requestUrl = generateArchesURL("arches_search:datatype_facets", {
        datatype: datatype,
    });

    const response = await fetch(requestUrl, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        },
    });

    const parsed = await response.json();
    if (!response.ok) {
        throw new Error((parsed && parsed.message) || response.statusText);
    }

    return parsed;
}
