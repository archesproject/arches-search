from functools import partial

from django.db import transaction
from arches.app.functions.base import BaseFunction
from arches.app.models.models import EditLog, TileModel
from arches.app.models.resource import Resource
from arches.app.models.system_settings import settings
from arches.app.models.tile import Tile
from arches_search.indexing.index_descriptor import (
    build_descriptor_terms,
    write_descriptor_search_terms,
)
from arches_search.indexing.index_from_tile import SEARCH_MODELS, index_from_tile
from arches_search.indexing.indexing_factory import IndexingFactory
from arches_search.models.models import TermSearch


def _refresh_descriptor_search_terms(resourceinstance_id):
    resource = (
        Resource.objects.select_related("graph").filter(pk=resourceinstance_id).first()
    )
    if resource is None:
        return
    resource.save_descriptors(descriptors=("name",))
    write_descriptor_search_terms(resource)


def _queue_descriptor_refresh(resourceinstance_id):
    resourceinstance_id = str(resourceinstance_id)
    connection = transaction.get_connection()
    for _savepoint_ids, callback, _robust in connection.run_on_commit:
        is_queued = getattr(callback, "func", None) is _refresh_descriptor_search_terms
        if is_queued and callback.args == (resourceinstance_id,):
            return
    transaction.on_commit(
        partial(_refresh_descriptor_search_terms, resourceinstance_id), robust=True
    )


class SearchIndexingFunction(BaseFunction):
    # occurs after Tile.save
    def post_save(self, *args, **kwargs):
        tile: Tile = args[0]
        nodegroup_cache = kwargs.get("nodegroup_cache", {})
        index_records = index_from_tile(tile, nodegroup_cache=nodegroup_cache)
        for record in index_records:
            record.save()

        _queue_descriptor_refresh(tile.resourceinstance_id)

    def delete(self, *args, **kwargs):
        tile: Tile = args[0]
        _queue_descriptor_refresh(tile.resourceinstance_id)

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
        descriptor_cache = {}

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
            for resource in Resource.objects.filter(pk__in=batch).select_related(
                "graph"
            ):
                values_to_index[TermSearch].extend(
                    build_descriptor_terms(resource, descriptor_cache)
                )

            # replace each resource's rows wholesale so tiles edited or
            # removed by the load don't leave stale values behind
            with transaction.atomic():
                for model, values in values_to_index.items():
                    model.objects.filter(resourceinstanceid__in=batch).delete()
                    model.objects.bulk_create(values, batch_size=batch_size)
