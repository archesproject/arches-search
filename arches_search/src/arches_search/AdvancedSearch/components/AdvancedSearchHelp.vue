<script setup lang="ts">
import { useGettext } from "vue3-gettext";

import Accordion from "openvue/accordion";
import AccordionContent from "openvue/accordioncontent";
import AccordionHeader from "openvue/accordionheader";
import AccordionPanel from "openvue/accordionpanel";

const { $gettext } = useGettext();
</script>

<template>
    <div class="advanced-search-help">
        <h3 class="advanced-search-help-title">
            <i
                aria-hidden="true"
                class="pi pi-question-circle"
            />
            <span>{{ $gettext("How to use Advanced Search") }}</span>
        </h3>

        <Accordion :value="[]">
            <AccordionPanel value="model">
                <AccordionHeader>
                    {{ $gettext("1. Select a resource model") }}
                </AccordionHeader>
                <AccordionContent>
                    <div class="advanced-search-help-section">
                        <p>
                            {{
                                $gettext(
                                    "Every advanced search looks for one resource model. Choose it in the sentence at the top before adding conditions.",
                                )
                            }}
                        </p>
                        <p>
                            {{
                                $gettext(
                                    "Changing the model after adding conditions asks first, because the conditions belong to the previous model.",
                                )
                            }}
                        </p>
                    </div>
                </AccordionContent>
            </AccordionPanel>

            <AccordionPanel value="conditions">
                <AccordionHeader>
                    {{ $gettext("2. Add conditions") }}
                </AccordionHeader>
                <AccordionContent>
                    <div class="advanced-search-help-section">
                        <p>
                            <strong>{{ $gettext("Attribute") }}</strong>
                            <span>
                                {{
                                    $gettext("filters on a field of the model.")
                                }}
                            </span>
                        </p>
                        <p>
                            {{
                                $gettext(
                                    "Picking a date field makes it a time filter, and a location field a map filter. Their values are set in the side panel.",
                                )
                            }}
                        </p>
                        <p>
                            <strong>{{ $gettext("Relationship") }}</strong>
                            <span>
                                {{
                                    $gettext(
                                        "follows a link field to another resource model. Conditions inside it filter those related records; with none, any related record counts.",
                                    )
                                }}
                            </span>
                        </p>
                        <p>
                            {{
                                $gettext(
                                    "NOT on a condition matches the records the condition would leave out.",
                                )
                            }}
                        </p>
                    </div>
                </AccordionContent>
            </AccordionPanel>

            <AccordionPanel value="logic">
                <AccordionHeader>
                    {{ $gettext("3. ALL and ANY") }}
                </AccordionHeader>
                <AccordionContent>
                    <div class="advanced-search-help-section">
                        <p>
                            {{
                                $gettext(
                                    "ALL means every condition must match. ANY means at least one must.",
                                )
                            }}
                        </p>
                        <p>
                            {{
                                $gettext(
                                    "The AND or OR between conditions follows their group's ALL or ANY, and clicking it switches the whole group. To mix them, put conditions in a group of their own.",
                                )
                            }}
                        </p>
                    </div>
                </AccordionContent>
            </AccordionPanel>

            <AccordionPanel value="groups">
                <AccordionHeader>
                    {{ $gettext("4. Group conditions") }}
                </AccordionHeader>
                <AccordionContent>
                    <div class="advanced-search-help-section">
                        <p>
                            {{
                                $gettext(
                                    "Groups nest logic, for example (A AND B) OR C. Each group has its own ALL or ANY, and a new group starts with the opposite of the group it sits in.",
                                )
                            }}
                        </p>
                        <p>
                            {{
                                $gettext(
                                    "Select to group wraps conditions you check in a new group. They must sit in the same group.",
                                )
                            }}
                        </p>
                        <p>
                            {{
                                $gettext(
                                    "A label is optional and makes the query description easier to read.",
                                )
                            }}
                        </p>
                    </div>
                </AccordionContent>
            </AccordionPanel>

            <AccordionPanel value="run">
                <AccordionHeader>
                    {{ $gettext("5. Run, describe and save") }}
                </AccordionHeader>
                <AccordionContent>
                    <div class="advanced-search-help-section">
                        <p>
                            {{
                                $gettext(
                                    "Search runs the query. The line beside Clear all describes it as you build it, and Describe Query shows it in full.",
                                )
                            }}
                        </p>
                        <p>
                            {{
                                $gettext(
                                    "Save Search keeps the query on its own, and Export Results exports what Search found. Simple Search also uses the query, alongside its own filters, while its model is selected there.",
                                )
                            }}
                        </p>
                    </div>
                </AccordionContent>
            </AccordionPanel>
        </Accordion>
    </div>
</template>

<style scoped>
.advanced-search-help {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    padding: 2rem;
}

.advanced-search-help .advanced-search-help-title {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 0;
    color: var(--p-text-color);
    font-size: 1.5rem;
    font-weight: 700;
}

.advanced-search-help .advanced-search-help-title .pi {
    color: var(--p-primary-color);
}

.advanced-search-help .advanced-search-help-section {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
}

.advanced-search-help p {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 0;
    color: var(--p-text-muted-color);
    font-size: 1.3rem;
    line-height: 1.5;
}
</style>
