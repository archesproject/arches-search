from typing import Dict, Tuple, Optional

from django.utils.translation import gettext as _
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
            facet_key = (facet.datatype.datatype, facet.operator)
            self._facet_by_datatype_and_operator[facet_key] = facet

    def get_facet(
        self, subject_datatype_name: str, operator_token: str
    ) -> AdvancedSearchFacet:
        facet = self._facet_by_datatype_and_operator.get(
            (subject_datatype_name, operator_token)
        )

        if facet is None:
            raise AdvancedSearchFacet.DoesNotExist(
                _(
                    "No facet found for datatype '%(datatype)s' with operator '%(operator)s'"
                )
                % {"datatype": subject_datatype_name, "operator": operator_token}
            )
        return facet

    def resolve_positive_facet(
        self, operator_token: str, datatype_name: str
    ) -> Optional[AdvancedSearchFacet]:
        candidate = self._facet_by_datatype_and_operator.get(
            (datatype_name, operator_token)
        )

        if candidate and candidate.is_orm_template_negated:
            reverse_operator = f"POSITIVE_OF::{operator_token}"
            return self._facet_by_datatype_and_operator.get(
                (datatype_name, reverse_operator)
            )

        return None

    def presence_implies_match(
        self, subject_datatype_name: str, operator_token: str
    ) -> bool:
        facet = self.get_facet(subject_datatype_name, operator_token)
        return facet.arity == 0 and bool(facet.is_orm_template_negated)
