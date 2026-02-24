import { LogicToken } from "@/arches_search/AdvancedSearch/types.ts";
import type {
    AdvancedSearchFacet,
    GraphModel,
    GroupPayload,
    LiteralClause,
    LiteralOperand,
    NodeMetadataEntry,
    NodeMetadataMap,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

type GettextFunction = (
    messageId: string,
    interpolationValues?: Record<string, unknown>,
) => string;

type NodeLabelResolver = (
    graphSlug: string,
    nodeAlias: string,
) => string | undefined;

type DescribeQueryOptions = {
    payload: GroupPayload;
    graphs: readonly GraphModel[];
    datatypesToAdvancedSearchFacets: Readonly<
        Record<string, AdvancedSearchFacet[]>
    >;
    gettext: GettextFunction;
    getNodeLabel?: NodeLabelResolver;
    nodeMetadata?: NodeMetadataMap;
};

type OperatorLabelMap = Record<string, string>;

type PathOperand = {
    type: "PATH";
    value: unknown;
};

type Operand = LiteralOperand | PathOperand;

type TraversalQuantifier = "ANY" | "ALL" | "NONE";

const TRAVERSAL_ANY = "ANY" as const;
const TRAVERSAL_ALL = "ALL" as const;
const TRAVERSAL_NONE = "NONE" as const;

const LESS_THAN_ALIASES: readonly string[] = ["<", "&lt;"];
const GREATER_THAN_ALIASES: readonly string[] = [">", "&gt;"];
const LESS_THAN_OR_EQUAL_ALIASES: readonly string[] = [
    "<=",
    "≤",
    "&lt;=",
    "&le;",
];
const GREATER_THAN_OR_EQUAL_ALIASES: readonly string[] = [
    ">=",
    "≥",
    "&gt;=",
    "&ge;",
];
const EQUAL_ALIASES: readonly string[] = ["=", "=="];
const NOT_EQUAL_ALIASES: readonly string[] = ["!=", "<>", "≠", "&ne;"];

export function describeAdvancedSearchQuery(
    options: DescribeQueryOptions,
): string {
    const {
        payload,
        graphs,
        datatypesToAdvancedSearchFacets,
        gettext,
        getNodeLabel,
        nodeMetadata,
    } = options;

    if (!payload || !payload.graph_slug) {
        return "";
    }

    const operatorLabelMap = buildOperatorLabelMap(
        datatypesToAdvancedSearchFacets,
        gettext,
    );
    const graphLabel = resolveGraphLabel(payload.graph_slug, graphs);
    const conditionDescription = describeGroupConditions(
        payload,
        graphs,
        operatorLabelMap,
        gettext,
        getNodeLabel,
        nodeMetadata,
    );

    if (!conditionDescription) {
        return gettext("Find all %{graph} instances.", { graph: graphLabel });
    }

    if (startsWithPredicateFragment(payload)) {
        return gettext("Find all %{graph} instances that %{conditions}.", {
            graph: graphLabel,
            conditions: conditionDescription,
        });
    }

    return gettext("Find all %{graph} instances where %{conditions}.", {
        graph: graphLabel,
        conditions: conditionDescription,
    });
}

function startsWithPredicateFragment(groupPayload: GroupPayload): boolean {
    if (groupPayload.clauses.length > 0) {
        return false;
    }

    if (
        groupPayload.relationship !== null &&
        groupPayload.relationship.path.length > 0
    ) {
        return true;
    }

    if (groupPayload.groups.length === 0) {
        return false;
    }

    return startsWithPredicateFragment(groupPayload.groups[0]);
}

function buildOperatorLabelMap(
    datatypesToAdvancedSearchFacets: Readonly<
        Record<string, AdvancedSearchFacet[]>
    >,
    gettext: GettextFunction,
): OperatorLabelMap {
    const operatorLabelMap: OperatorLabelMap = {};

    for (const facetList of Object.values(datatypesToAdvancedSearchFacets)) {
        for (const facet of facetList) {
            if (!facet.operator || operatorLabelMap[facet.operator]) {
                continue;
            }
            const normalizedLabel = normalizeOperatorLabel(
                facet.label.trim(),
                gettext,
            );
            operatorLabelMap[facet.operator] =
                normalizedLabel || facet.operator;
        }
    }

    return operatorLabelMap;
}

function normalizeOperatorLabel(
    rawLabel: string,
    gettext: GettextFunction,
): string {
    const label = rawLabel.trim();
    if (!label) {
        return "";
    }

    if (LESS_THAN_ALIASES.includes(label)) {
        return gettext("is less than");
    }

    if (GREATER_THAN_ALIASES.includes(label)) {
        return gettext("is greater than");
    }

    if (LESS_THAN_OR_EQUAL_ALIASES.includes(label)) {
        return gettext("is less than or equal to");
    }

    if (GREATER_THAN_OR_EQUAL_ALIASES.includes(label)) {
        return gettext("is greater than or equal to");
    }

    if (EQUAL_ALIASES.includes(label)) {
        return gettext("is equal to");
    }

    if (NOT_EQUAL_ALIASES.includes(label)) {
        return gettext("is not equal to");
    }

    return label;
}

function resolveGraphLabel(
    graphSlug: string,
    graphs: readonly GraphModel[],
): string {
    return graphs.find((graph) => graph.slug === graphSlug)?.name ?? graphSlug;
}

function getNodeMetadataForNode(
    graphSlug: string,
    nodeAlias: string,
    nodeMetadata: NodeMetadataMap | undefined,
): NodeMetadataEntry | undefined {
    if (!nodeMetadata) {
        return undefined;
    }

    const keyWithSpace = `('${graphSlug}', '${nodeAlias}')`;
    const keyWithoutSpace = `('${graphSlug}','${nodeAlias}')`;

    return nodeMetadata[keyWithSpace] ?? nodeMetadata[keyWithoutSpace];
}

function resolveNodeLabel(
    graphSlug: string,
    nodeAlias: string,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    const widgetLabel = getNodeMetadataForNode(
        graphSlug,
        nodeAlias,
        nodeMetadata,
    )?.card_x_node_x_widget_label?.trim();

    if (widgetLabel) {
        return widgetLabel;
    }

    if (getNodeLabel) {
        const resolvedLabel = getNodeLabel(graphSlug, nodeAlias);
        if (resolvedLabel) {
            return resolvedLabel;
        }
    }

    return nodeAlias;
}

function formatValueList(values: string[], gettext: GettextFunction): string {
    const trimmedValues = values
        .map((v) => v.trim())
        .filter((v) => v.length > 0);
    const count = trimmedValues.length;

    if (count === 0) {
        return "";
    }

    if (count === 1) {
        return trimmedValues[0];
    }

    if (count === 2) {
        return gettext("%{first} and %{second}", {
            first: trimmedValues[0],
            second: trimmedValues[1],
        });
    }

    const allButLast = trimmedValues.slice(0, -1).join(", ");
    const lastValue = trimmedValues[count - 1];

    return gettext("%{list}, and %{last}", {
        list: allButLast,
        last: lastValue,
    });
}

function joinManyWithLogic(
    parts: string[],
    logicToken: LogicToken,
    gettext: GettextFunction,
): string {
    const trimmedParts = parts.map((p) => p.trim()).filter((p) => p.length > 0);
    const count = trimmedParts.length;

    if (count === 0) {
        return "";
    }

    if (count === 1) {
        return trimmedParts[0];
    }

    if (count === 2) {
        const left = trimmedParts[0];
        const right = trimmedParts[1];

        if (logicToken === LogicToken.OR) {
            return gettext("%{left}, or %{right}", { left, right });
        }

        return gettext("%{left}, and %{right}", { left, right });
    }

    const allButLast = trimmedParts.slice(0, -1).join(", ");
    const lastPart = trimmedParts[count - 1];

    if (logicToken === LogicToken.OR) {
        return gettext("%{list}, or %{last}", {
            list: allButLast,
            last: lastPart,
        });
    }

    return gettext("%{list}, and %{last}", {
        list: allButLast,
        last: lastPart,
    });
}

function resolveTraversalQuantifier(
    quantifiers: readonly string[],
): TraversalQuantifier {
    const first = quantifiers[0];
    if (first === TRAVERSAL_ALL || first === TRAVERSAL_NONE) {
        return first;
    }
    return TRAVERSAL_ANY;
}

function describeGroupConditions(
    groupPayload: GroupPayload,
    graphs: readonly GraphModel[],
    operatorLabelMap: OperatorLabelMap,
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    const conditionDescriptions: string[] = [];

    for (const clause of groupPayload.clauses) {
        const description = describeClause(
            clause,
            graphs,
            operatorLabelMap,
            gettext,
            getNodeLabel,
            nodeMetadata,
        );
        if (description) {
            conditionDescriptions.push(description);
        }
    }

    if (
        groupPayload.relationship !== null &&
        groupPayload.relationship.path.length > 0
    ) {
        const relatedGroup = groupPayload.groups[0];
        const relationshipDescription = describeRelationshipCondition(
            groupPayload.relationship,
            relatedGroup,
            graphs,
            operatorLabelMap,
            gettext,
            getNodeLabel,
            nodeMetadata,
        );
        if (relationshipDescription) {
            conditionDescriptions.push(relationshipDescription);
        }

        for (const nestedGroup of groupPayload.groups.slice(1)) {
            const nestedDescription = describeGroupConditions(
                nestedGroup,
                graphs,
                operatorLabelMap,
                gettext,
                getNodeLabel,
                nodeMetadata,
            );
            if (nestedDescription) {
                conditionDescriptions.push(nestedDescription);
            }
        }
    } else {
        for (const nestedGroup of groupPayload.groups) {
            const nestedDescription = describeGroupConditions(
                nestedGroup,
                graphs,
                operatorLabelMap,
                gettext,
                getNodeLabel,
                nodeMetadata,
            );
            if (nestedDescription) {
                conditionDescriptions.push(nestedDescription);
            }
        }
    }

    if (conditionDescriptions.length === 0) {
        return "";
    }

    return joinManyWithLogic(
        conditionDescriptions,
        groupPayload.logic,
        gettext,
    );
}

function describeClause(
    clause: LiteralClause,
    graphs: readonly GraphModel[],
    operatorLabelMap: OperatorLabelMap,
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    if (clause.subject.length === 0) {
        return "";
    }

    const [subjectGraphSlug, subjectNodeAlias] =
        clause.subject[clause.subject.length - 1];

    const fieldLabel = resolveNodeLabel(
        subjectGraphSlug,
        subjectNodeAlias,
        getNodeLabel,
        nodeMetadata,
    ).trim();

    const operatorLabel = (
        (clause.operator && operatorLabelMap[clause.operator]) ||
        clause.operator
    ).trim();

    if (!fieldLabel || !operatorLabel) {
        return "";
    }

    const subjectDatatype =
        getNodeMetadataForNode(subjectGraphSlug, subjectNodeAlias, nodeMetadata)
            ?.datatype ?? "";

    const operandDescriptions: string[] = [];

    for (const operand of clause.operands as Operand[]) {
        const description = describeOperand(
            operand,
            graphs,
            gettext,
            getNodeLabel,
            subjectDatatype,
            nodeMetadata,
        );
        if (description) {
            operandDescriptions.push(description);
        }
    }

    const valuePhrase = formatValueList(operandDescriptions, gettext).trim();

    if (valuePhrase) {
        return gettext("%{field} %{operator} %{value}", {
            field: fieldLabel,
            operator: operatorLabel,
            value: valuePhrase,
        });
    }

    return gettext("%{field} %{operator}", {
        field: fieldLabel,
        operator: operatorLabel,
    });
}

function describeOperand(
    operand: Operand,
    graphs: readonly GraphModel[],
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    subjectDatatype: string,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    if (operand.type === "PATH") {
        return describePathOperand(
            operand.value,
            graphs,
            gettext,
            getNodeLabel,
            nodeMetadata,
        );
    }

    const operandWithDisplay = operand as LiteralOperand & {
        display_value?: unknown;
    };
    const preferredValue =
        "display_value" in operandWithDisplay
            ? operandWithDisplay.display_value
            : operand.value;

    if (preferredValue === null || typeof preferredValue === "undefined") {
        return "";
    }

    if (
        subjectDatatype === "string" &&
        preferredValue &&
        typeof preferredValue === "object" &&
        !Array.isArray(preferredValue)
    ) {
        const entries = Object.entries(
            preferredValue as Record<string, unknown>,
        );

        if (entries.length === 1) {
            const [languageCode, rawValue] = entries[0];

            if (typeof rawValue === "string") {
                const trimmedValue = rawValue.trim();
                const trimmedLanguageCode = languageCode.trim();

                if (trimmedValue && trimmedLanguageCode) {
                    return gettext("%{value} (%{language})", {
                        value: trimmedValue,
                        language: trimmedLanguageCode,
                    }).trim();
                }

                if (trimmedValue) {
                    return trimmedValue;
                }
            }
        }
    }

    return String(preferredValue).trim();
}

function describePathOperand(
    value: unknown,
    graphs: readonly GraphModel[],
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    if (!Array.isArray(value) || value.length === 0) {
        return "";
    }

    const lastPathEntry = value[value.length - 1];

    if (!Array.isArray(lastPathEntry) || lastPathEntry.length !== 2) {
        return "";
    }

    const [graphSlug, nodeAlias] = lastPathEntry as [string, string];

    const graphLabel = resolveGraphLabel(graphSlug, graphs).trim();
    const fieldLabel = resolveNodeLabel(
        graphSlug,
        nodeAlias,
        getNodeLabel,
        nodeMetadata,
    ).trim();

    if (graphLabel && fieldLabel) {
        return gettext("the %{field} field in %{graph}", {
            field: fieldLabel,
            graph: graphLabel,
        });
    }

    if (graphLabel) {
        return graphLabel;
    }

    if (fieldLabel) {
        return gettext("the %{field} field", { field: fieldLabel });
    }

    return "";
}

function describeRelationshipCondition(
    relationship: RelationshipBlock,
    relatedGroup: GroupPayload | undefined,
    graphs: readonly GraphModel[],
    operatorLabelMap: OperatorLabelMap,
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    if (relationship.path.length !== 1) {
        return "";
    }

    const [relatedGraphSlug, relatedNodeAlias] = relationship.path[0];

    const relatedGraphLabel = resolveGraphLabel(relatedGraphSlug, graphs);
    const relationshipFieldLabel = resolveNodeLabel(
        relatedGraphSlug,
        relatedNodeAlias,
        getNodeLabel,
        nodeMetadata,
    );

    const traversalQuantifier = resolveTraversalQuantifier(
        relationship.traversal_quantifiers,
    );

    const innerConditions = relatedGroup
        ? describeGroupConditions(
              relatedGroup,
              graphs,
              operatorLabelMap,
              gettext,
              getNodeLabel,
              nodeMetadata,
          ).trim()
        : "";

    const hasInnerConditions = innerConditions.length > 0;
    const isInverse = relationship.is_inverse;

    if (isInverse) {
        if (traversalQuantifier === TRAVERSAL_ALL) {
            if (hasInnerConditions) {
                return gettext(
                    "are the %{field} of all %{graph} instances where %{conditions}",
                    {
                        field: relationshipFieldLabel,
                        graph: relatedGraphLabel,
                        conditions: innerConditions,
                    },
                );
            }

            return gettext("are the %{field} of all %{graph} instances", {
                field: relationshipFieldLabel,
                graph: relatedGraphLabel,
            });
        }

        if (traversalQuantifier === TRAVERSAL_NONE) {
            if (hasInnerConditions) {
                return gettext(
                    "are the %{field} of no %{graph} instances where %{conditions}",
                    {
                        field: relationshipFieldLabel,
                        graph: relatedGraphLabel,
                        conditions: innerConditions,
                    },
                );
            }

            return gettext("are the %{field} of no %{graph} instances", {
                field: relationshipFieldLabel,
                graph: relatedGraphLabel,
            });
        }

        if (hasInnerConditions) {
            return gettext(
                "are the %{field} of any %{graph} instances where %{conditions}",
                {
                    field: relationshipFieldLabel,
                    graph: relatedGraphLabel,
                    conditions: innerConditions,
                },
            );
        }

        return gettext("are the %{field} of any %{graph} instances", {
            field: relationshipFieldLabel,
            graph: relatedGraphLabel,
        });
    }

    if (traversalQuantifier === TRAVERSAL_ALL) {
        if (hasInnerConditions) {
            return gettext("have only %{field} where %{conditions}", {
                field: relationshipFieldLabel,
                conditions: innerConditions,
            });
        }

        return gettext("have only %{field}", { field: relationshipFieldLabel });
    }

    if (traversalQuantifier === TRAVERSAL_NONE) {
        if (hasInnerConditions) {
            return gettext("have no %{field} where %{conditions}", {
                field: relationshipFieldLabel,
                conditions: innerConditions,
            });
        }

        return gettext("have no %{field}", { field: relationshipFieldLabel });
    }

    if (hasInnerConditions) {
        return gettext("have at least one %{field} where %{conditions}", {
            field: relationshipFieldLabel,
            conditions: innerConditions,
        });
    }

    return gettext("have at least one %{field}", {
        field: relationshipFieldLabel,
    });
}
