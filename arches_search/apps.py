from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Tags, Warning, register


class ArchesSearchConfig(AppConfig):
    name = "arches_search"
    is_arches_application = True

    search_indexers = [
        "arches_search.indexing.indexers.boolean.BooleanIndexing",
        "arches_search.indexing.indexers.concept.ConceptIndexing",
        "arches_search.indexing.indexers.concept_list.ConceptListIndexing",
        "arches_search.indexing.indexers.date.DateIndexing",
        "arches_search.indexing.indexers.edtf.EDTFIndexing",
        "arches_search.indexing.indexers.file_list.FileListIndexing",
        "arches_search.indexing.indexers.geojson_feature_collection.GeoJSONFeatureCollectionIndexing",
        "arches_search.indexing.indexers.non_localized_string.NonLocalizedStringIndexing",
        "arches_search.indexing.indexers.number.NumberIndexing",
        "arches_search.indexing.indexers.reference.ReferenceIndexing",
        "arches_search.indexing.indexers.resource_instance.ResourceInstanceIndexing",
        "arches_search.indexing.indexers.resource_instance_list.ResourceInstanceListIndexing",
        "arches_search.indexing.indexers.string.StringIndexing",
        "arches_search.indexing.indexers.url.URLIndexing",
    ]

    advanced_search_operand_normalizers = [
        "arches_search.utils.advanced_search.operand_normalization.normalizers.date.DateOperandNormalizer",
        "arches_search.utils.advanced_search.operand_normalization.normalizers.edtf.EDTFOperandNormalizer",
        "arches_search.utils.advanced_search.operand_normalization.normalizers.geojson_feature_collection.GeojsonFeatureCollectionOperandNormalizer",
        "arches_search.utils.advanced_search.operand_normalization.normalizers.reference.ReferenceOperandNormalizer",
        "arches_search.utils.advanced_search.operand_normalization.normalizers.resource_instance.ResourceInstanceOperandNormalizer",
        "arches_search.utils.advanced_search.operand_normalization.normalizers.resource_instance_list.ResourceInstanceListOperandNormalizer",
        "arches_search.utils.advanced_search.operand_normalization.normalizers.string.StringOperandNormalizer",
        "arches_search.utils.advanced_search.operand_normalization.normalizers.url.URLOperandNormalizer",
    ]

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
