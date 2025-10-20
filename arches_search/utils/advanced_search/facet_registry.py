from typing import Dict, Tuple

from arches_search.models.models import AdvancedSearchFacet


class FacetRegistry:
    def __init__(self) -> None:
        self._facet_by_datatype_and_operator: Dict[
            Tuple[str, str], AdvancedSearchFacet
        ] = {}

        queryset = AdvancedSearchFacet.objects.select_related("datatype").only(
            "arity",
            "orm_template",
            "is_orm_template_negated",
            "operator",
            "datatype__datatype",
        )

        for facet in queryset:
            self._facet_by_datatype_and_operator[
                (facet.datatype.datatype, facet.operator)
            ] = facet

    def get_facet(
        self, subject_datatype_name: str, operator_token: str
    ) -> AdvancedSearchFacet:
        facet = self._facet_by_datatype_and_operator.get(
            (subject_datatype_name, operator_token)
        )

        if facet is None:
            raise AdvancedSearchFacet.DoesNotExist

        return facet
