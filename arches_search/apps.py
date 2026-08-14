from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Tags, Warning, register


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


@register(Tags.compatibility)
def warn_default_allow_permission_framework(app_configs, **kwargs):
    errors = []

    if (
        getattr(settings, "PERMISSION_FRAMEWORK", None)
        == "arches_default_allow.ArchesDefaultAllowPermissionFramework"
    ):
        errors.append(
            Warning(
                msg="arches-search is not compatible with Default Allow permission framework.",
                hint="Set PERMISSION_FRAMEWORK to arches_default_deny.ArchesDefaultDenyPermissionFramework.",
                obj=settings.APP_NAME,
                id="arches_search.W001",
            )
        )

    return errors
