import cytoscape from "cytoscape";
import cola from "cytoscape-cola";

let isColaRegistered = false;

// Cytoscape layouts are registered on the library itself, once
export function registerCytoscapeLayouts(): void {
    if (isColaRegistered) return;
    cytoscape.use(cola);
    isColaRegistered = true;
}
