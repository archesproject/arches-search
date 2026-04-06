import {
    ClauseSubjectTypeToken,
    LogicToken,
} from "@/arches_search/AdvancedSearch/types.ts";
import type {
    AdvancedSearchFacet,
    GraphModel,
    GroupPayload,
    LiteralClause,
    LiteralOperand,
    NodeMetadataMap,
    RelationshipBlock,
} from "@/arches_search/AdvancedSearch/types.ts";

export type DescribeQueryOptions = {
    payload: GroupPayload;
    graphs: readonly GraphModel[];
    datatypesToAdvancedSearchFacets: Readonly<
        Record<string, AdvancedSearchFacet[]>
    >;
    gettext: (msgid: string, params?: Record<string, unknown>) => string;
    nodeMetadata?: NodeMetadataMap;
    resourceNames?: Readonly<Record<string, string>>;
};

const TRAVERSAL_ALL = "ALL" as const;
const TRAVERSAL_NONE = "NONE" as const;

export function describeAdvancedSearchQuery(
    options: DescribeQueryOptions,
): string {
    const {
        payload,
        graphs,
        datatypesToAdvancedSearchFacets,
        gettext,
        nodeMetadata,
        resourceNames,
    } = options;

    if (!payload?.graph_slug) {
        return "";
    }

    const operatorLabelMap = buildOperatorLabelMap();
    const graphLabel = resolveGraphLabel(payload.graph_slug);
    const conditionDescription = describeGroupConditions(payload);

    if (!conditionDescription) {
        return gettext("Find all %{graph} instances.", { graph: graphLabel });
    }

    if (startsWithPredicateFragment(payload)) {
        return gettext("Find all %{graph} instances %{conditions}.", {
            graph: graphLabel,
            conditions: conditionDescription,
        });
    }

    return gettext("Find all %{graph} instances where %{conditions}.", {
        graph: graphLabel,
        conditions: conditionDescription,
    });

    function buildOperatorLabelMap() {
        const symbolLabels: Record<string, string> = {
            LESS_THAN: gettext("is less than"),
            GREATER_THAN: gettext("is greater than"),
            LESS_THAN_OR_EQUALS: gettext("is less than or equal to"),
            GREATER_THAN_OR_EQUALS: gettext("is greater than or equal to"),
            EQUALS: gettext("equals"),
            NOT_EQUALS: gettext("does not equal"),
        };
        const labelsByOperatorKey: Record<string, string> = {};
        for (const facetList of Object.values(
            datatypesToAdvancedSearchFacets,
        )) {
            for (const facet of facetList) {
                if (!facet.operator || labelsByOperatorKey[facet.operator]) {
                    continue;
                }
                labelsByOperatorKey[facet.operator] =
                    symbolLabels[facet.operator] ?? facet.label;
            }
        }
        return labelsByOperatorKey;
    }

    function resolveGraphLabel(graphSlug: string) {
        return (
            graphs.find((graph) => graph.slug === graphSlug)?.name ?? graphSlug
        );
    }

    function getNodeMetadata(graphSlug: string, nodeAlias: string) {
        if (!nodeMetadata) {
            return undefined;
        }
        const keyWithSpace = `('${graphSlug}', '${nodeAlias}')`;
        const keyWithoutSpace = `('${graphSlug}','${nodeAlias}')`;
        return nodeMetadata[keyWithSpace] ?? nodeMetadata[keyWithoutSpace];
    }

    function resolveFieldLabel(graphSlug: string, nodeAlias: string) {
        return (
            getNodeMetadata(
                graphSlug,
                nodeAlias,
            )?.card_x_node_x_widget_label?.trim() || nodeAlias
        );
    }

    function formatValueList(values: string[]) {
        const nonEmptyValues = values
            .map((value) => value.trim())
            .filter(Boolean);
        if (nonEmptyValues.length === 0) {
            return "";
        }
        if (nonEmptyValues.length === 1) {
            return nonEmptyValues[0];
        }
        if (nonEmptyValues.length === 2) {
            return gettext("%{first_value} and %{second_value}", {
                first_value: nonEmptyValues[0],
                second_value: nonEmptyValues[1],
            });
        }
        return gettext("%{values_list}, and %{last_value}", {
            values_list: nonEmptyValues.slice(0, -1).join(", "),
            last_value: nonEmptyValues[nonEmptyValues.length - 1],
        });
    }

    function joinConditionList(conditions: string[], logic: LogicToken) {
        const nonEmptyConditions = conditions
            .map((condition) => condition.trim())
            .filter(Boolean);
        if (nonEmptyConditions.length === 0) {
            return "";
        }
        if (nonEmptyConditions.length === 1) {
            return nonEmptyConditions[0];
        }

        const allButLastCondition = nonEmptyConditions.slice(0, -1).join(", ");
        const lastCondition = nonEmptyConditions[nonEmptyConditions.length - 1];

        if (nonEmptyConditions.length === 2) {
            if (logic === LogicToken.OR) {
                return gettext("%{first_condition} or %{second_condition}", {
                    first_condition: nonEmptyConditions[0],
                    second_condition: nonEmptyConditions[1],
                });
            }
            return gettext("%{first_condition} and %{second_condition}", {
                first_condition: nonEmptyConditions[0],
                second_condition: nonEmptyConditions[1],
            });
        }

        if (logic === LogicToken.OR) {
            return gettext("%{conditions_list}, or %{last_condition}", {
                conditions_list: allButLastCondition,
                last_condition: lastCondition,
            });
        }
        return gettext("%{conditions_list}, and %{last_condition}", {
            conditions_list: allButLastCondition,
            last_condition: lastCondition,
        });
    }

    function describeGroupConditions(groupPayload: GroupPayload): string {
        const conditionDescriptions: string[] = [];

        for (const clause of groupPayload.clauses) {
            const clauseDescription = describeClause(clause);
            if (clauseDescription) {
                conditionDescriptions.push(clauseDescription);
            }
        }

        if (
            groupPayload.relationship !== null &&
            groupPayload.relationship.path.graph_slug &&
            groupPayload.relationship.path.node_alias
        ) {
            const relationshipDescription = describeRelationship(
                groupPayload.relationship,
                groupPayload.groups[0],
            );
            if (relationshipDescription) {
                conditionDescriptions.push(relationshipDescription);
            }

            for (const nestedGroupPayload of groupPayload.groups.slice(1)) {
                const nestedGroupDescription =
                    describeGroupConditions(nestedGroupPayload);
                if (nestedGroupDescription) {
                    conditionDescriptions.push(nestedGroupDescription);
                }
            }
        } else {
            for (const nestedGroupPayload of groupPayload.groups) {
                const nestedGroupDescription =
                    describeGroupConditions(nestedGroupPayload);
                if (nestedGroupDescription) {
                    conditionDescriptions.push(nestedGroupDescription);
                }
            }
        }

        return joinConditionList(conditionDescriptions, groupPayload.logic);
    }

    function describeClause(clause: LiteralClause) {
        const subjectGraphSlug = clause.subject.graph_slug?.trim();
        if (!subjectGraphSlug) {
            return "";
        }

        const subjectNodeAlias =
            clause.subject.type === ClauseSubjectTypeToken.NODE
                ? clause.subject.node_alias
                : "";
        const rawOperator = clause.operator?.trim();
        const fieldLabel = resolveClauseFieldLabel(clause).trim();
        const operatorLabel = rawOperator
            ? (operatorLabelMap[rawOperator] ?? rawOperator).trim()
            : "";

        if (!fieldLabel || !operatorLabel) {
            return "";
        }

        const subjectDatatype = subjectNodeAlias
            ? getNodeMetadata(subjectGraphSlug, subjectNodeAlias)?.datatype ??
              ""
            : "";
        const operandDescriptions: string[] = [];

        for (const operand of clause.operands as (
            | LiteralOperand
            | { type: "PATH"; value: unknown }
        )[]) {
            const operandDescription = describeOperand(
                operand,
                subjectDatatype,
            );
            if (operandDescription) {
                operandDescriptions.push(operandDescription);
            }
        }

        const valuePhrase = formatValueList(operandDescriptions).trim();

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

    function resolveClauseFieldLabel(clause: LiteralClause) {
        const subjectGraphSlug = clause.subject.graph_slug?.trim();
        if (!subjectGraphSlug) {
            return "";
        }

        if (
            clause.subject.type === ClauseSubjectTypeToken.NODE &&
            clause.subject.node_alias
        ) {
            return resolveFieldLabel(
                subjectGraphSlug,
                clause.subject.node_alias,
            );
        }

        if (
            clause.subject.type === ClauseSubjectTypeToken.SEARCH_MODELS &&
            clause.subject.search_models.length > 0
        ) {
            const graphLabel = resolveGraphLabel(subjectGraphSlug).trim();
            if (graphLabel) {
                return gettext("any field in %{graph}", {
                    graph: graphLabel,
                });
            }

            return gettext("any field");
        }

        return "";
    }

    function describeOperand(
        operand: LiteralOperand | { type: "PATH"; value: unknown },
        subjectDatatype: string,
    ) {
        if (operand.type === "PATH") {
            return describePathValue(operand.value);
        }

        const rawValue = operand.display_value ?? operand.value;

        if (rawValue === null || typeof rawValue === "undefined") {
            return "";
        }

        if (Array.isArray(rawValue)) {
            const resolvedNames = (rawValue as unknown[])
                .filter((item): item is string => typeof item === "string")
                .map((resourceId) => resourceNames?.[resourceId] || resourceId);
            return formatValueList(resolvedNames);
        }

        if (
            subjectDatatype === "string" &&
            typeof rawValue === "object" &&
            !Array.isArray(rawValue)
        ) {
            const localeValueEntries = Object.entries(
                rawValue as Record<string, unknown>,
            );
            if (localeValueEntries.length === 1) {
                const [languageCode, localizedStringValue] =
                    localeValueEntries[0];
                if (typeof localizedStringValue === "string") {
                    const trimmedValue = localizedStringValue.trim();
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

        return String(rawValue).trim();
    }

    function describePathValue(value: unknown) {
        if (!Array.isArray(value) || value.length === 0) {
            return "";
        }

        const lastPathEntry = value[value.length - 1];
        if (!Array.isArray(lastPathEntry) || lastPathEntry.length !== 2) {
            return "";
        }

        const [pathGraphSlug, pathNodeAlias] = lastPathEntry as [
            string,
            string,
        ];
        const pathGraphLabel = resolveGraphLabel(pathGraphSlug).trim();
        const pathFieldLabel = resolveFieldLabel(
            pathGraphSlug,
            pathNodeAlias,
        ).trim();

        if (pathGraphLabel && pathFieldLabel) {
            return gettext("the %{field} field in %{graph}", {
                field: pathFieldLabel,
                graph: pathGraphLabel,
            });
        }
        if (pathGraphLabel) {
            return pathGraphLabel;
        }
        if (pathFieldLabel) {
            return gettext("the %{field} field", { field: pathFieldLabel });
        }
        return "";
    }

    function describeRelationship(
        relationship: RelationshipBlock,
        relatedGroupPayload?: GroupPayload,
    ) {
        if (!relationship.path.graph_slug || !relationship.path.node_alias) {
            return "";
        }

        const relatedGraphSlug = relationship.path.graph_slug;
        const relatedNodeAlias = relationship.path.node_alias;
        const relatedGraphLabel = resolveGraphLabel(relatedGraphSlug);
        const relationshipFieldLabel = resolveFieldLabel(
            relatedGraphSlug,
            relatedNodeAlias,
        );
        const traversalQuantifier = resolveTraversalQuantifier(
            relationship.traversal_quantifier,
        );
        let innerConditions = "";
        if (relatedGroupPayload) {
            innerConditions =
                describeGroupConditions(relatedGroupPayload).trim();
        }
        const hasInnerConditions = innerConditions.length > 0;

        if (relationship.is_inverse) {
            if (traversalQuantifier === TRAVERSAL_ALL) {
                if (hasInnerConditions) {
                    return gettext(
                        "that are the %{field} of all %{graph} instances where %{conditions}",
                        {
                            field: relationshipFieldLabel,
                            graph: relatedGraphLabel,
                            conditions: innerConditions,
                        },
                    );
                }
                return gettext(
                    "that are the %{field} of all %{graph} instances",
                    {
                        field: relationshipFieldLabel,
                        graph: relatedGraphLabel,
                    },
                );
            }
            if (traversalQuantifier === TRAVERSAL_NONE) {
                if (hasInnerConditions) {
                    return gettext(
                        "that are the %{field} of no %{graph} instances where %{conditions}",
                        {
                            field: relationshipFieldLabel,
                            graph: relatedGraphLabel,
                            conditions: innerConditions,
                        },
                    );
                }
                return gettext(
                    "that are the %{field} of no %{graph} instances",
                    {
                        field: relationshipFieldLabel,
                        graph: relatedGraphLabel,
                    },
                );
            }
            if (hasInnerConditions) {
                return gettext(
                    "that are the %{field} of any %{graph} instances where %{conditions}",
                    {
                        field: relationshipFieldLabel,
                        graph: relatedGraphLabel,
                        conditions: innerConditions,
                    },
                );
            }
            return gettext("that are the %{field} of any %{graph} instances", {
                field: relationshipFieldLabel,
                graph: relatedGraphLabel,
            });
        }

        if (traversalQuantifier === TRAVERSAL_ALL) {
            if (hasInnerConditions) {
                return gettext("that have only %{field} where %{conditions}", {
                    field: relationshipFieldLabel,
                    conditions: innerConditions,
                });
            }
            return gettext("that have only %{field}", {
                field: relationshipFieldLabel,
            });
        }

        if (traversalQuantifier === TRAVERSAL_NONE) {
            if (hasInnerConditions) {
                return gettext("that have no %{field} where %{conditions}", {
                    field: relationshipFieldLabel,
                    conditions: innerConditions,
                });
            }
            return gettext("that have no %{field}", {
                field: relationshipFieldLabel,
            });
        }

        if (hasInnerConditions) {
            return gettext(
                "that have at least one %{field} where %{conditions}",
                {
                    field: relationshipFieldLabel,
                    conditions: innerConditions,
                },
            );
        }
        return gettext("that have at least one %{field}", {
            field: relationshipFieldLabel,
        });
    }
}

function startsWithPredicateFragment(groupPayload: GroupPayload): boolean {
    if (groupPayload.clauses.length > 0) {
        return false;
    }
    if (
        groupPayload.relationship !== null &&
        groupPayload.relationship.path.graph_slug &&
        groupPayload.relationship.path.node_alias
    ) {
        return true;
    }
    if (groupPayload.groups.length === 0) {
        return false;
    }
    return startsWithPredicateFragment(groupPayload.groups[0]);
}

function resolveTraversalQuantifier(quantifier: string) {
    if (quantifier === TRAVERSAL_ALL || quantifier === TRAVERSAL_NONE) {
        return quantifier;
    }
    return "ANY";
}
