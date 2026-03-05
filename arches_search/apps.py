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
