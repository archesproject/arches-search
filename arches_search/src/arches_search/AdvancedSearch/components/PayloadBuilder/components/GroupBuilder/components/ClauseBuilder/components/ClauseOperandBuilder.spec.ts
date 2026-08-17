import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/PayloadBuilder/components/GroupBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";

import type { GraphModel, Node } from "@/arches_search/AdvancedSearch/types.ts";

const subjectTerminalNode = { alias: "related_resource" } as Node;
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
});
