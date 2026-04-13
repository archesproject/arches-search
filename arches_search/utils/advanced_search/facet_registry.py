from typing import Dict, Optional, Tuple

from django.utils.translation import gettext as _

from arches_search.models.models import AdvancedSearchFacet


class FacetRegistry:
    def __init__(self) -> None:
        self._facet_by_datatype_and_operator: Dict[
            Tuple[str, str], AdvancedSearchFacet
        ] = {}
        self._facet_by_datatype_operator_and_model: Dict[
            Tuple[str, str, object], AdvancedSearchFacet
        ] = {}

        queryset = AdvancedSearchFacet.objects.select_related(
            "datatype", "target_search_model"
        )

        for facet in queryset:
            datatype_name = facet.datatype.datatype
            operator_token = facet.operator
            model_class = facet.target_model_class

            self._facet_by_datatype_and_operator.setdefault(
                (datatype_name, operator_token), facet
            )
            if model_class is not None:
                self._facet_by_datatype_operator_and_model[
                    (datatype_name, operator_token, model_class)
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

    def get_facet_for_model(
        self,
        subject_datatype_name: str,
        operator_token: str,
        model_class,
    ) -> AdvancedSearchFacet:
        facet = self._facet_by_datatype_operator_and_model.get(
            (subject_datatype_name, operator_token, model_class)
        )

        if facet is None:
            raise AdvancedSearchFacet.DoesNotExist(
                _(
                    "No facet found for datatype '%(datatype)s', operator '%(operator)s', "
                    "model '%(model)s'"
                )
                % {
                    "datatype": subject_datatype_name,
                    "operator": operator_token,
                    "model": model_class.__name__,
                }
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
