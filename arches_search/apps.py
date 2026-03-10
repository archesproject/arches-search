from django.apps import AppConfig


class ArchesSearchConfig(AppConfig):
    name = "arches_search"
    is_arches_application = True

    def ready(self):
        from arches_modular_reports.config_generator_registry import register

        register(
            "search",
            lambda _: {
                "name": "Search Result",
                "theme": "",
                "components": [
                    {
                        "component": "arches_search/SearchResults/components/DescriptorSection",
                        "config": {},
                    }
                ],
            },
        )

        def search_result_expanded_factory(graph):
            from arches_modular_reports.models import ReportConfig

            rc = ReportConfig(graph=graph)
            sections = rc.generate_card_sections()[:1]
            components = sections[0]["components"] if sections else []
            return {
                "name": "Search Result Expanded",
                "theme": "",
                "components": components,
            }

        register("search_result_expanded", search_result_expanded_factory)
