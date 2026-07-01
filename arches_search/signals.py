"""Keep the descriptor term index fresh on resource save.

``Resource.save_descriptors`` persists the recomputed descriptors via
``super().save()``, which fires ``post_save`` with the fresh descriptors on the
instance — so we reindex the descriptor there. Connected from
ArchesSearchConfig.ready().
"""
import logging

from django.db.models.signals import post_save

from arches.app.models.models import ResourceInstance
from arches.app.models.resource import Resource
from arches.app.models.system_settings import settings

from arches_search.indexing.index_descriptor import index_resource_descriptors

logger = logging.getLogger(__name__)


def _index_descriptor(sender, instance, **kwargs):
    if str(instance.graph_id) == str(settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID):
        return
    try:
        index_resource_descriptors(instance)
    except Exception:
        # Never let descriptor indexing break a resource save (e.g. the search
        # tables not existing yet during an initial migrate).
        logger.debug(
            "Descriptor term indexing skipped for resource %s",
            getattr(instance, "pk", None),
            exc_info=True,
        )


def connect():
    post_save.connect(
        _index_descriptor,
        sender=Resource,
        dispatch_uid="arches_search.descriptor_index.resource",
    )
    post_save.connect(
        _index_descriptor,
        sender=ResourceInstance,
        dispatch_uid="arches_search.descriptor_index.resourceinstance",
    )
