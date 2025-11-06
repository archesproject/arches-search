from typing import Dict, Tuple, Optional, Sequence, Any

from django.db.models import Q
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
            raise AdvancedSearchFacet.DoesNotExist(
                _(
                    "No facet found for datatype '%(datatype)s' with operator '%(operator)s'"
                )
                % {"datatype": subject_datatype_name, "operator": operator_token}
            )
        return facet

    def get_positive_facet_for(
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

    def predicate(
        self,
        subject_datatype_name: str,
        operator_token: str,
        column_name: str,
        params: Sequence[Any],
    ) -> tuple[Q | Dict[str, Any], bool]:
        facet = self.get_facet(subject_datatype_name, operator_token)
        lookup_key = (facet.orm_template or "").replace("{col}", column_name)
        is_template_negated = bool(facet.is_orm_template_negated)
        single_value: Any = params[0] if params else True
        kwargs = {lookup_key: single_value}
        return (~Q(**kwargs), True) if is_template_negated else (kwargs, False)
