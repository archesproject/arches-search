import { useReferenceSelectOptionsStore } from "@/arches_controlled_lists/stores/useReferenceSelectOptionsStore.ts";

import type {
    ReferenceSelectLabel,
    ReferenceSelectNodeValue,
} from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

type ReferenceOption = {
    uri: string;
    list_item_values: ReferenceSelectLabel[];
    children?: ReferenceOption[];
};

export function isLabelList(value: unknown): value is string[] {
    return (
        Array.isArray(value) &&
        value.length > 0 &&
        value.every((item) => typeof item === "string")
    );
}

// Simple Search saves a reference filter as the labels it matched, but the
// reference widget shows list items, so each label is found in the node's list.
export async function referenceValuesForLabels(
    graphSlug: string,
    nodeAlias: string,
    listId: string,
    labels: string[],
): Promise<ReferenceSelectNodeValue[]> {
    // The store's items are option details rather than the tree nodes its type
    // declares; the reference widget reads them the same way.
    const options = (await useReferenceSelectOptionsStore().fetchWidgetOptions(
        graphSlug,
        nodeAlias,
    )) as unknown as ReferenceOption[];
    const allOptions = flattenOptions(options);

    return labels.flatMap((label) => {
        const matchingOption = allOptions.find((option) =>
            option.list_item_values.some(
                (itemLabel) => itemLabel.value === label,
            ),
        );
        if (!matchingOption) {
            return [];
        }
        return [
            {
                list_id: listId,
                uri: matchingOption.uri,
                labels: matchingOption.list_item_values,
            },
        ];
    });
}

function flattenOptions(options: ReferenceOption[]): ReferenceOption[] {
    return options.flatMap((option) => [
        option,
        ...flattenOptions(option.children ?? []),
    ]);
}
