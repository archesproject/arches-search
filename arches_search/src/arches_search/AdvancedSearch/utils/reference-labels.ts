import arches from "arches";

import { getItemLabel } from "@/arches_controlled_lists/utils.ts";
import { useReferenceSelectOptionsStore } from "@/arches_controlled_lists/stores/useReferenceSelectOptionsStore.ts";

import type { Language } from "@/arches_controlled_lists/types.ts";
import type {
    ReferenceSelectLabel,
    ReferenceSelectNodeValue,
} from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

const DEFAULT_LANGUAGE_CODE = "en";

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

export function isReferenceValueList(
    value: unknown,
): value is ReferenceSelectNodeValue[] {
    return (
        Array.isArray(value) &&
        value.every(
            (item) =>
                typeof item === "object" &&
                item !== null &&
                "uri" in item &&
                "labels" in item,
        )
    );
}

export function referenceValueLabel(
    referenceValue: ReferenceSelectNodeValue,
): string {
    const systemLanguageCode =
        arches.languages.find((language: Language) => language.isdefault)
            ?.code ?? DEFAULT_LANGUAGE_CODE;
    return getItemLabel(
        referenceValue,
        arches.activeLanguage,
        systemLanguageCode,
    ).value;
}

// A reference value saved as plain labels, as Simple Search once saved its
// filters, is shown as list items by finding each label in the node's list.
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
    const referenceValues = flattenOptions(options).map((option) => ({
        list_id: listId,
        uri: option.uri,
        labels: option.list_item_values,
    }));
    return referenceValuesWithLabels(referenceValues, labels);
}

export function referenceValuesWithLabels(
    referenceValues: ReferenceSelectNodeValue[],
    labels: string[],
): ReferenceSelectNodeValue[] {
    return labels.flatMap((label) => {
        const matchingReferenceValue = referenceValues.find((referenceValue) =>
            referenceValue.labels.some(
                (itemLabel) => itemLabel.value === label,
            ),
        );
        if (!matchingReferenceValue) {
            return [];
        }
        return [matchingReferenceValue];
    });
}

function flattenOptions(options: ReferenceOption[]): ReferenceOption[] {
    return options.flatMap((option) => [
        option,
        ...flattenOptions(option.children ?? []),
    ]);
}
