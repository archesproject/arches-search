import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ClauseOperandBuilder from "@/arches_search/AdvancedSearch/components/QueryBuilder/components/ClauseBuilder/components/ClauseOperandBuilder.vue";

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
            },
            global: {
                stubs: { GenericWidget: GenericWidgetStub },
            },
        });

        const widget = wrapper.findComponent(GenericWidgetStub);
        expect(widget.props("aliasedNodeData")).toBeUndefined();
    });

    it("hands the widget's own edits back to it, keeping every language", async () => {
        const wrapper = mount(ClauseOperandBuilder, {
            props: {
                subjectTerminalNode,
                subjectTerminalGraph,
                modelValue: null,
            },
            global: {
                stubs: { GenericWidget: GenericWidgetStub },
            },
        });
        const editedAliasedNodeData = {
            node_value: {
                en: { value: "Barcelona", direction: "ltr" },
                fr: { value: "Barcelone", direction: "ltr" },
            },
            display_value: "Barcelone",
            details: [],
        };

        const widget = wrapper.findComponent(GenericWidgetStub);
        widget.vm.$emit("update:aliasedNodeData", editedAliasedNodeData);
        await wrapper.vm.$nextTick();

        expect(widget.props("aliasedNodeData")).toEqual(editedAliasedNodeData);
        expect(wrapper.emitted("update:modelValue")?.[0]).toEqual([
            {
                type: "LITERAL",
                value: editedAliasedNodeData.node_value,
                display_value: "Barcelone",
            },
        ]);
    });
});
