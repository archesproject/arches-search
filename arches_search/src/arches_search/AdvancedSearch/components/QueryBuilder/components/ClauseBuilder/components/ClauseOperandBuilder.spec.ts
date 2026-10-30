import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";

import type { GraphModel, Node } from "@/arches_search/AdvancedSearch/types.ts";

const GLASS_ITEM = {
    list_id: "material-list",
    uri: "http://example.com/glass",
    labels: [
        {
            id: "label-1",
            language_id: "en",
            list_item_id: "glass-item",
            value: "glass",
            valuetype_id: "prefLabel",
        },
    ],
};

vi.mock(
    "@/arches_search/AdvancedSearch/utils/reference-labels.ts",
    async (importOriginal) => ({
        ...(await importOriginal<object>()),
        referenceValuesForLabels: vi.fn(async () => [GLASS_ITEM]),
    }),
);

const subjectTerminalNode = { alias: "related_resource" } as Node;
const materialNode = {
    alias: "material",
    datatype: "reference",
    config: { controlledList: "material-list" },
} as unknown as Node;
const subjectTerminalGraph = { slug: "test_graph" } as GraphModel;

const GenericWidgetStub = {
    name: "GenericWidget",
    props: [
        "mode",
        "graphSlug",
        "nodeAlias",
        "shouldShowLabel",
        "value",
        "aliasedNodeData",
    ],
    template: "<div />",
};

describe("ClauseOperandBuilder hydration", () => {
    it("rebuilds aliased-node-data from a loaded resource-instance operand", () => {
        const wrapper = mount(ClauseOperandBuilder, {
            props: {
                subjectTerminalNode,
                subjectTerminalGraph,
                modelValue: {
                    type: "LITERAL",
                    value: [
                        { resourceId: "9c9c9c9c-0000-0000-0000-000000000000" },
                    ],
                    display_value: "Amber Specimen",
                },
                operandType: "LITERAL",
            },
            global: {
                stubs: { GenericWidget: GenericWidgetStub },
            },
        });

        const widget = wrapper.findComponent(GenericWidgetStub);
        expect(widget.props("aliasedNodeData")).toEqual({
            node_value: [
                { resourceId: "9c9c9c9c-0000-0000-0000-000000000000" },
            ],
            display_value: "Amber Specimen",
            details: [],
        });
    });

    it("has no hydration data for a fresh clause with no stored value", () => {
        const wrapper = mount(ClauseOperandBuilder, {
            props: {
                subjectTerminalNode,
                subjectTerminalGraph,
                modelValue: null,
                operandType: "LITERAL",
            },
            global: {
                stubs: { GenericWidget: GenericWidgetStub },
            },
        });

        const widget = wrapper.findComponent(GenericWidgetStub);
        expect(widget.props("aliasedNodeData")).toBeUndefined();
    });

    it("has no hydration data for a PATH operand", () => {
        const wrapper = mount(ClauseOperandBuilder, {
            props: {
                subjectTerminalNode,
                subjectTerminalGraph,
                modelValue: {
                    type: "PATH",
                    value: [["test_graph", "some_alias"]],
                },
                operandType: "PATH",
            },
            global: {
                stubs: { GenericWidget: GenericWidgetStub },
            },
        });

        const widget = wrapper.findComponent(GenericWidgetStub);
        expect(widget.props("aliasedNodeData")).toBeUndefined();
        expect(widget.props("value")).toBeNull();
    });

    it("shows a reference saved as labels with its list items", async () => {
        const wrapper = mount(ClauseOperandBuilder, {
            props: {
                subjectTerminalNode: materialNode,
                subjectTerminalGraph,
                modelValue: { type: "LITERAL", value: ["glass"] },
                operandType: "LITERAL",
            },
            global: {
                stubs: { GenericWidget: GenericWidgetStub },
            },
        });

        expect(wrapper.findComponent(GenericWidgetStub).exists()).toBe(false);
        await flushPromises();

        expect(
            wrapper.findComponent(GenericWidgetStub).props("aliasedNodeData"),
        ).toEqual({
            node_value: [GLASS_ITEM],
            display_value: "glass",
            details: [],
        });
    });
});
