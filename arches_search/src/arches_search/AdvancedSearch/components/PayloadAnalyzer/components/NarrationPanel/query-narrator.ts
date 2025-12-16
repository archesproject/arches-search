import type {
    AdvancedSearchFacet,
    GroupPayload,
} from "@/arches_search/AdvancedSearch/types.ts";

export type GettextFunction = (
    messageId: string,
    interpolationValues?: Record<string, unknown>,
) => string;

type GraphSummary = {
    slug?: string;
    name?: string;
    label?: string;
    [key: string]: unknown;
};

type NodeLabelResolver = (
    graphSlug: string,
    nodeAlias: string,
) => string | undefined;

export type NodeMetadataEntry = {
    card_x_node_x_widget_label?: string;
    datatype?: string;
    [key: string]: unknown;
};

export type NodeMetadataMap = Readonly<Record<string, NodeMetadataEntry>>;

type DescribeQueryOptions = {
    payload: GroupPayload;
    graphs: readonly GraphSummary[];
    datatypesToAdvancedSearchFacets: Readonly<
        Record<string, AdvancedSearchFacet[]>
    >;
    gettext: GettextFunction;
    getNodeLabel?: NodeLabelResolver;
    nodeMetadata?: NodeMetadataMap;
};

type OperatorLabelMap = Record<string, string>;
type ClausePayload = GroupPayload["clauses"][number];
type OperandPayload =
    | ClausePayload["operands"][number]
    | {
          type: "PATH";
          value: unknown;
          [key: string]: unknown;
      };
type RelationshipState = NonNullable<GroupPayload["relationship"]>;

const LOGIC_AND = "AND" as const;
const LOGIC_OR = "OR" as const;
type LogicToken = typeof LOGIC_AND | typeof LOGIC_OR;

const TRAVERSAL_ANY = "ANY" as const;
const TRAVERSAL_ALL = "ALL" as const;
const TRAVERSAL_NONE = "NONE" as const;
type TraversalQuantifier =
    | typeof TRAVERSAL_ANY
    | typeof TRAVERSAL_ALL
    | typeof TRAVERSAL_NONE;

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

    const conditionDescription = describeRootConditions(
        payload,
        graphs,
        operatorLabelMap,
        gettext,
        getNodeLabel,
        nodeMetadata,
    );

    if (!conditionDescription) {
        return gettext("Find all %{graph} instances.", {
            graph: graphLabel,
        });
    }

    const shouldUseThatClause = startsWithPredicateFragment(payload);

    if (shouldUseThatClause) {
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
    const hasClauses =
        Array.isArray(groupPayload.clauses) && groupPayload.clauses.length > 0;
    if (hasClauses) {
        return false;
    }

    const relationshipState = groupPayload.relationship as
        | RelationshipState
        | undefined;

    const hasRelationshipPath =
        relationshipState &&
        Array.isArray(relationshipState.path) &&
        relationshipState.path.length > 0;

    if (hasRelationshipPath) {
        return true;
    }

    const hasGroups =
        Array.isArray(groupPayload.groups) && groupPayload.groups.length > 0;
    if (!hasGroups) {
        return false;
    }

    return startsWithPredicateFragment(groupPayload.groups[0] as GroupPayload);
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
            const facetWithOperator = facet as {
                operator?: unknown;
                label?: unknown;
            };

            const operatorKey =
                typeof facetWithOperator.operator === "string"
                    ? facetWithOperator.operator
                    : "";

            if (!operatorKey || operatorLabelMap[operatorKey]) {
                continue;
            }

            const rawLabel = facetWithOperator.label;
            const labelText = extractFacetLabelAsString(rawLabel).trim();
            const normalizedLabel = normalizeOperatorLabel(labelText, gettext);

            operatorLabelMap[operatorKey] =
                normalizedLabel.length > 0 ? normalizedLabel : operatorKey;
        }
    }

    return operatorLabelMap;
}

function extractFacetLabelAsString(rawLabel: unknown): string {
    if (typeof rawLabel === "string") {
        return rawLabel;
    }

    if (rawLabel && typeof rawLabel === "object") {
        for (const candidateValue of Object.values(
            rawLabel as Record<string, unknown>,
        )) {
            if (typeof candidateValue === "string") {
                return candidateValue;
            }
        }
    }

    return "";
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
    graphs: readonly GraphSummary[],
): string {
    const matchingGraph = graphs.find((graphSummary) => {
        return graphSummary.slug === graphSlug;
    });

    if (!matchingGraph) {
        return graphSlug;
    }

    if (typeof matchingGraph.label === "string" && matchingGraph.label) {
        return matchingGraph.label;
    }

    if (typeof matchingGraph.name === "string" && matchingGraph.name) {
        return matchingGraph.name;
    }

    return graphSlug;
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
    const nodeMetadataEntry = getNodeMetadataForNode(
        graphSlug,
        nodeAlias,
        nodeMetadata,
    );

    const widgetLabel = nodeMetadataEntry?.card_x_node_x_widget_label?.trim();
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
        .map((value) => value.trim())
        .filter((value) => value.length > 0);

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

function describeRootConditions(
    payload: GroupPayload,
    graphs: readonly GraphSummary[],
    operatorLabelMap: OperatorLabelMap,
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    const conditionDescriptions: string[] = [];

    if (Array.isArray(payload.clauses)) {
        for (const clausePayload of payload.clauses) {
            const clauseDescription = describeClause(
                clausePayload as ClausePayload,
                graphs,
                operatorLabelMap,
                gettext,
                getNodeLabel,
                nodeMetadata,
            );
            if (clauseDescription) {
                conditionDescriptions.push(clauseDescription);
            }
        }
    }

    const relationshipState = payload.relationship as
        | RelationshipState
        | undefined;
    const hasRelationshipPath =
        relationshipState &&
        Array.isArray(relationshipState.path) &&
        relationshipState.path.length > 0;

    if (hasRelationshipPath) {
        const relatedGroup =
            Array.isArray(payload.groups) && payload.groups.length > 0
                ? (payload.groups[0] as GroupPayload)
                : undefined;

        const relationshipDescription = describeRelationshipCondition(
            relationshipState as RelationshipState,
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

        if (Array.isArray(payload.groups) && payload.groups.length > 1) {
            for (const nestedGroupPayload of payload.groups.slice(1)) {
                const nestedDescription = describeGroupConditions(
                    nestedGroupPayload as GroupPayload,
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
    } else if (Array.isArray(payload.groups)) {
        for (const nestedGroupPayload of payload.groups) {
            const nestedDescription = describeGroupConditions(
                nestedGroupPayload as GroupPayload,
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

    const logicToken: LogicToken =
        payload.logic === LOGIC_OR ? LOGIC_OR : LOGIC_AND;

    return joinManyWithLogic(conditionDescriptions, logicToken, gettext);
}

function describeGroupConditions(
    groupPayload: GroupPayload,
    graphs: readonly GraphSummary[],
    operatorLabelMap: OperatorLabelMap,
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    const partDescriptions: string[] = [];

    if (Array.isArray(groupPayload.clauses)) {
        for (const clausePayload of groupPayload.clauses) {
            const clauseDescription = describeClause(
                clausePayload as ClausePayload,
                graphs,
                operatorLabelMap,
                gettext,
                getNodeLabel,
                nodeMetadata,
            );
            if (clauseDescription) {
                partDescriptions.push(clauseDescription);
            }
        }
    }

    const relationshipState = groupPayload.relationship as
        | RelationshipState
        | undefined;

    const hasRelationshipPath =
        relationshipState &&
        Array.isArray(relationshipState.path) &&
        relationshipState.path.length > 0;

    if (hasRelationshipPath) {
        const relatedGroup =
            Array.isArray(groupPayload.groups) && groupPayload.groups.length > 0
                ? (groupPayload.groups[0] as GroupPayload)
                : undefined;

        const relationshipDescription = describeRelationshipCondition(
            relationshipState as RelationshipState,
            relatedGroup,
            graphs,
            operatorLabelMap,
            gettext,
            getNodeLabel,
            nodeMetadata,
        );

        if (relationshipDescription) {
            partDescriptions.push(relationshipDescription);
        }

        if (
            Array.isArray(groupPayload.groups) &&
            groupPayload.groups.length > 1
        ) {
            for (const nestedGroupPayload of groupPayload.groups.slice(1)) {
                const nestedDescription = describeGroupConditions(
                    nestedGroupPayload as GroupPayload,
                    graphs,
                    operatorLabelMap,
                    gettext,
                    getNodeLabel,
                    nodeMetadata,
                );
                if (nestedDescription) {
                    partDescriptions.push(nestedDescription);
                }
            }
        }
    } else if (Array.isArray(groupPayload.groups)) {
        for (const nestedGroupPayload of groupPayload.groups) {
            const nestedDescription = describeGroupConditions(
                nestedGroupPayload as GroupPayload,
                graphs,
                operatorLabelMap,
                gettext,
                getNodeLabel,
                nodeMetadata,
            );
            if (nestedDescription) {
                partDescriptions.push(nestedDescription);
            }
        }
    }

    if (partDescriptions.length === 0) {
        return "";
    }

    const logicToken: LogicToken =
        groupPayload.logic === LOGIC_OR ? LOGIC_OR : LOGIC_AND;

    return joinManyWithLogic(partDescriptions, logicToken, gettext);
}

function describeClause(
    clausePayload: ClausePayload,
    graphs: readonly GraphSummary[],
    operatorLabelMap: OperatorLabelMap,
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    if (
        !Array.isArray(clausePayload.subject) ||
        clausePayload.subject.length === 0
    ) {
        return "";
    }

    const lastSubjectEntry =
        clausePayload.subject[clausePayload.subject.length - 1];

    if (!Array.isArray(lastSubjectEntry) || lastSubjectEntry.length !== 2) {
        return "";
    }

    const subjectGraphSlug = String(lastSubjectEntry[0]);
    const subjectNodeAlias = String(lastSubjectEntry[1]);

    const fieldLabel = resolveNodeLabel(
        subjectGraphSlug,
        subjectNodeAlias,
        getNodeLabel,
        nodeMetadata,
    ).trim();

    const operatorKey =
        typeof clausePayload.operator === "string"
            ? clausePayload.operator
            : "";

    const operatorLabelRaw =
        (operatorKey && operatorLabelMap[operatorKey]) || operatorKey;
    const operatorLabel = operatorLabelRaw.trim();

    if (!fieldLabel || !operatorLabel) {
        return "";
    }

    const operandsArray: OperandPayload[] = Array.isArray(
        clausePayload.operands,
    )
        ? (clausePayload.operands as OperandPayload[])
        : [];

    const subjectNodeMetadata = getNodeMetadataForNode(
        subjectGraphSlug,
        subjectNodeAlias,
        nodeMetadata,
    );
    const subjectDatatype =
        typeof subjectNodeMetadata?.datatype === "string"
            ? subjectNodeMetadata.datatype
            : "";

    const operandDescriptions: string[] = [];

    for (const operandPayload of operandsArray) {
        const operandDescription = describeOperand(
            operandPayload,
            graphs,
            gettext,
            getNodeLabel,
            subjectDatatype,
            nodeMetadata,
        );
        if (operandDescription) {
            operandDescriptions.push(operandDescription);
        }
    }

    const valuePhrase = formatValueList(operandDescriptions, gettext).trim();

    if (valuePhrase) {
        return gettext("the value of the %{field} node %{operator} %{value}", {
            field: fieldLabel,
            operator: operatorLabel,
            value: valuePhrase,
        });
    }

    return gettext("the %{field} node %{operator}", {
        field: fieldLabel,
        operator: operatorLabel,
    });
}

function describeOperand(
    operandPayload: OperandPayload,
    graphs: readonly GraphSummary[],
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    subjectDatatype: string,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    if (!operandPayload) {
        return "";
    }

    if (operandPayload.type === "PATH") {
        return describePathOperand(
            operandPayload.value,
            graphs,
            gettext,
            getNodeLabel,
            nodeMetadata,
        );
    }

    const typedOperand = operandPayload as {
        display_value?: unknown;
        value?: unknown;
    };

    const preferredValue =
        "display_value" in typedOperand
            ? typedOperand.display_value
            : typedOperand.value;

    if (preferredValue === null || typeof preferredValue === "undefined") {
        return "";
    }

    const isStringDatatype = subjectDatatype === "string";

    if (
        isStringDatatype &&
        preferredValue &&
        typeof preferredValue === "object" &&
        !Array.isArray(preferredValue)
    ) {
        const entries = Object.entries(
            preferredValue as Record<string, unknown>,
        );

        if (entries.length === 1) {
            const [languageCodeRaw, rawValue] = entries[0];
            const languageCode = String(languageCodeRaw).trim();

            if (typeof rawValue === "string") {
                const trimmedValue = rawValue.trim();

                if (trimmedValue && languageCode) {
                    return gettext("%{value} (%{language})", {
                        value: trimmedValue,
                        language: languageCode,
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
    graphs: readonly GraphSummary[],
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

    const graphSlug = String(lastPathEntry[0]);
    const nodeAlias = String(lastPathEntry[1]);

    const graphLabel = resolveGraphLabel(graphSlug, graphs).trim();
    const fieldLabel = resolveNodeLabel(
        graphSlug,
        nodeAlias,
        getNodeLabel,
        nodeMetadata,
    ).trim();

    const hasGraphLabel = graphLabel.length > 0;
    const hasFieldLabel = fieldLabel.length > 0;

    if (hasGraphLabel && hasFieldLabel) {
        return gettext("the %{graph} %{field} node", {
            graph: graphLabel,
            field: fieldLabel,
        });
    }

    if (hasGraphLabel) {
        return graphLabel;
    }

    if (hasFieldLabel) {
        return gettext("the %{field} node", {
            field: fieldLabel,
        });
    }

    return "";
}

function joinManyWithLogic(
    parts: string[],
    logicToken: LogicToken,
    gettext: GettextFunction,
): string {
    const trimmedParts = parts
        .map((part) => part.trim())
        .filter((part) => part.length > 0);

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

        if (logicToken === LOGIC_OR) {
            return gettext("%{left}, or %{right}", {
                left,
                right,
            });
        }

        return gettext("%{left}, and %{right}", {
            left,
            right,
        });
    }

    const allButLast = trimmedParts.slice(0, -1).join(", ");
    const lastPart = trimmedParts[count - 1];

    if (logicToken === LOGIC_OR) {
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

function describeRelationshipCondition(
    relationshipState: RelationshipState,
    relatedGroup: GroupPayload | undefined,
    graphs: readonly GraphSummary[],
    operatorLabelMap: OperatorLabelMap,
    gettext: GettextFunction,
    getNodeLabel: NodeLabelResolver | undefined,
    nodeMetadata: NodeMetadataMap | undefined,
): string {
    if (!Array.isArray(relationshipState.path)) {
        return "";
    }

    if (relationshipState.path.length !== 1) {
        return "";
    }

    const singleLeg = relationshipState.path[0];

    if (!Array.isArray(singleLeg) || singleLeg.length !== 2) {
        return "";
    }

    const relatedGraphSlug = String(singleLeg[0]);
    const relatedNodeAlias = String(singleLeg[1]);

    const relatedGraphLabel = resolveGraphLabel(relatedGraphSlug, graphs);
    const relationshipFieldLabel = resolveNodeLabel(
        relatedGraphSlug,
        relatedNodeAlias,
        getNodeLabel,
        nodeMetadata,
    );

    const traversalQuantifier = resolveTraversalQuantifier(
        relationshipState.traversal_quantifiers,
    );

    let innerConditions = "";
    if (relatedGroup) {
        innerConditions = describeGroupConditions(
            relatedGroup,
            graphs,
            operatorLabelMap,
            gettext,
            getNodeLabel,
            nodeMetadata,
        ).trim();
    }

    const hasInnerConditions = innerConditions.length > 0;
    const isInverse = Boolean(relationshipState.is_inverse);

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

        return gettext("have only %{field}", {
            field: relationshipFieldLabel,
        });
    }

    if (traversalQuantifier === TRAVERSAL_NONE) {
        if (hasInnerConditions) {
            return gettext("have no %{field} where %{conditions}", {
                field: relationshipFieldLabel,
                conditions: innerConditions,
            });
        }

        return gettext("have no %{field}", {
            field: relationshipFieldLabel,
        });
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

function resolveTraversalQuantifier(
    rawQuantifiers: unknown,
): TraversalQuantifier {
    if (Array.isArray(rawQuantifiers) && rawQuantifiers.length > 0) {
        const [firstQuantifier] = rawQuantifiers as TraversalQuantifier[];

        if (
            firstQuantifier === TRAVERSAL_ANY ||
            firstQuantifier === TRAVERSAL_ALL ||
            firstQuantifier === TRAVERSAL_NONE
        ) {
            return firstQuantifier;
        }
    }

    return TRAVERSAL_ANY;
}
