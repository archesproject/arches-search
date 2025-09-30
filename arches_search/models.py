from django.db import models

from django.utils.translation import gettext_lazy as _

from arches.app.models.models import DDataType
from arches_controlled_lists.models import List


class DatatypeXAdvancedSearchFacets(models.Model):
    datatype = models.ForeignKey(
        DDataType,
        on_delete=models.CASCADE,
        db_column="datatypeid",
        verbose_name=_("Data Type"),
        help_text=_("The data type to which the advanced search facets apply."),
    )
    controlled_list = models.ForeignKey(
        List,
        on_delete=models.CASCADE,
        db_column="controlledlistid",
        verbose_name=_("Controlled List"),
        help_text=_(
            "The controlled list associated with the data type, if applicable."
        ),
        null=True,
        blank=True,
    )
