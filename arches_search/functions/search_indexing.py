from django.db import transaction
from arches.app.functions.base import BaseFunction
from arches.app.models.models import EditLog, TileModel
from arches.app.models.system_settings import settings
from arches.app.models.tile import Tile
from arches_search.indexing.index_from_tile import SEARCH_MODELS, index_from_tile
from arches_search.indexing.indexing_factory import IndexingFactory


class SearchIndexingFunction(BaseFunction):
    # occurs after Tile.save
    def post_save(self, *args, **kwargs):
        tile: Tile = args[0]
        nodegroup_cache = kwargs.get("nodegroup_cache", {})
        index_records = index_from_tile(tile, nodegroup_cache=nodegroup_cache)
        for record in index_records:
            record.save()

    # occurs after a bulk load, which writes tiles without calling Tile.save
    def post_import(self, transaction_id, *args, **kwargs):
        resourceids = list(
            EditLog.objects.filter(transactionid=transaction_id)
            .exclude(resourceinstanceid=str(settings.SYSTEM_SETTINGS_RESOURCE_ID))
            .values_list("resourceinstanceid", flat=True)
            .distinct()
        )
        batch_size = settings.INDEX_BATCH_SIZE
        nodegroup_cache = {}
        indexing_factory = IndexingFactory()

        for start in range(0, len(resourceids), batch_size):
            batch = resourceids[start : start + batch_size]
            values_to_index = {model: [] for model in SEARCH_MODELS}
            for tile in TileModel.objects.filter(
                resourceinstance_id__in=batch
            ).iterator(chunk_size=batch_size):
                for val in (
                    index_from_tile(
                        tile,
                        delete_existing=False,
                        indexing_factory=indexing_factory,
                        nodegroup_cache=nodegroup_cache,
                    )
                    or []
                ):
                    values_to_index[type(val)].append(val)

            # replace each resource's rows wholesale so tiles edited or
            # removed by the load don't leave stale values behind
            with transaction.atomic():
                for model, values in values_to_index.items():
                    model.objects.filter(resourceinstanceid__in=batch).delete()
                    model.objects.bulk_create(values, batch_size=batch_size)
