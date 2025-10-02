import { generateArchesURL } from "@/arches/utils/generate-arches-url.ts";

export async function getGraphs() {
    const response = await fetch(
        generateArchesURL("arches:get_graph_models_api"),
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        },
    );

    const parsed = await response.json();
    if (!response.ok) throw new Error(parsed.message || response.statusText);

    return parsed;
}
