from django.conf import settings
from django.utils.translation import get_language

from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase
from arches.app.models import models as arches_models


class NodeAliasesWithWidgetLabelsForGraphAPI(APIBase):
    def get(self, request, graph_id):
        language_code = get_language() or settings.LANGUAGE_CODE
        base_language_code = language_code.split("-")[0]
        default_language_code = settings.LANGUAGE_CODE

        card_node_widget_rows = arches_models.CardXNodeXWidget.objects.filter(
            node__graph_id=graph_id
        ).order_by("node__name", "sortorder")

        response_items = []
        for card_node_widget in card_node_widget_rows:
            label = card_node_widget.label
            label_value = (
                label.get(language_code)
                or label.get(base_language_code)
                or label.get(default_language_code)
                or str(label)
            )

            response_items.append(
                {
                    "node_alias": card_node_widget.node.alias,
                    "card_x_node_x_widget_label": label_value,
                }
            )

        return JSONResponse(response_items)
