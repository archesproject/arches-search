import cytoscape from "cytoscape";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { syncGraphElements } from "@/arches_search/RelationshipGraph/utils/sync-graph-elements.ts";

import type { Core, ElementDefinition } from "cytoscape";

function node(id: string, label = id, classes = ""): ElementDefinition {
    return { group: "nodes", data: { id, label }, classes };
}

function edge(id: string, source: string, target: string): ElementDefinition {
    return { group: "edges", data: { id, source, target } };
}

describe("syncGraphElements", () => {
    let cy: Core;

    beforeEach(() => {
        cy = cytoscape({ headless: true, styleEnabled: false });
    });

    afterEach(() => {
        cy.destroy();
    });

    it("adds seeds before neighbors and returns only new node ids", () => {
        const result = syncGraphElements(
            cy,
            [node("neighbor"), node("seed", "Seed", "seed")],
            [edge("link", "seed", "neighbor")],
            () => 0.5,
        );
        expect(result.addedNodeIds).toEqual(["seed", "neighbor"]);
        expect(cy.nodes().length).toBe(2);
        expect(cy.edges().length).toBe(1);
        const seedPosition = cy.getElementById("seed").position();
        const neighborPosition = cy.getElementById("neighbor").position();
        expect(
            Math.hypot(
                neighborPosition.x - seedPosition.x,
                neighborPosition.y - seedPosition.y,
            ),
        ).toBeCloseTo(120);
    });

    it("keeps existing positions while updating data and classes", () => {
        cy.add(node("seed"));
        cy.getElementById("seed").position({ x: 25, y: 80 });
        const result = syncGraphElements(
            cy,
            [node("seed", "Updated <name>", "on-path seed")],
            [],
            () => 0.5,
        );
        expect(result.addedNodeIds).toEqual([]);
        expect(cy.getElementById("seed").position()).toEqual({ x: 25, y: 80 });
        expect(cy.getElementById("seed").data("label")).toBe("Updated <name>");
        expect(cy.getElementById("seed").classes().sort()).toEqual([
            "on-path",
            "seed",
        ]);
    });

    it("does not rewrite unchanged data or reordered classes", () => {
        cy.add(node("seed", "Seed", "seed on-path"));
        const onData = vi.fn();
        const onClass = vi.fn();
        cy.on("data", onData);
        cy.on("class", onClass);
        syncGraphElements(cy, [node("seed", "Seed", "on-path seed")], []);
        expect(onData).not.toHaveBeenCalled();
        expect(onClass).not.toHaveBeenCalled();
    });

    it("removes obsolete elements and ignores edges with missing endpoints", () => {
        cy.add([node("keep"), node("old"), edge("old-link", "keep", "old")]);
        syncGraphElements(
            cy,
            [node("keep"), node("new")],
            [edge("valid", "keep", "new"), edge("dangling", "keep", "deleted")],
            () => 0.5,
        );
        expect(
            cy
                .elements()
                .map((element) => element.id())
                .sort(),
        ).toEqual(["keep", "new", "valid"]);
    });

    it("clears the canvas for an empty selection", () => {
        cy.add([node("one"), node("two"), edge("link", "one", "two")]);
        expect(syncGraphElements(cy, [], []).addedNodeIds).toEqual([]);
        expect(cy.elements().length).toBe(0);
    });

    it("supports self relationships and parallel edges", () => {
        syncGraphElements(
            cy,
            [node("one"), node("two")],
            [
                edge("self", "one", "one"),
                edge("first", "one", "two"),
                edge("second", "one", "two"),
            ],
        );
        expect(cy.edges().length).toBe(3);
    });
});
