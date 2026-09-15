from django.core.management.base import BaseCommand

from arches.app.models import models
from arches.app.models.system_settings import settings

from arches_search.models.models import NodeFilterConfig

FILTERABLE_DATATYPES = ("reference", "number")


class Command(BaseCommand):
    """
    Commands for managing node filter configurations

    """

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=["generate"],
            help='"generate" (create filter configs for all the graphs).',
        )

        parser.add_argument(
            "-g",
            "--graph",
            action="store",
            dest="graph",
            default="all",
            help='Graph slug to operate on. Defaults to "all".',
        )

        parser.add_argument(
            "--overwrite",
            action="store_true",
            dest="overwrite",
            default=False,
            help="Generate filter configs",
        )

    def handle(self, *args, **options):
        if options["operation"] == "generate":
            self.generate_filter_configs(
                graph_slug=options["graph"],
                overwrite=options["overwrite"],
            )

    def generate_filter_configs(self, graph_slug=None, overwrite=False):
        eligible_graphs = models.GraphModel.objects.filter(
            isresource=True,
            slug__isnull=False,
            source_identifier=None,
        ).exclude(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)

        if graph_slug and graph_slug != "all":
            eligible_graphs = eligible_graphs.filter(slug=graph_slug)
            if not eligible_graphs.exists():
                self.stderr.write(
                    self.style.ERROR(
                        f'No eligible graph found with slug "{graph_slug}".'
                    )
                )
                return

        if overwrite:
            existing_count = NodeFilterConfig.objects.filter(
                graph__in=eligible_graphs,
                slug="filtering",
            ).count()
            targeting_all = not graph_slug or graph_slug == "all"
            if targeting_all or existing_count:
                graph_label = "all graphs" if targeting_all else f'graph "{graph_slug}"'
                confirm = input(
                    f"This will overwrite {existing_count} existing config(s) across {graph_label}. Continue? [y/N] "
                )
                if confirm.strip().lower() != "y":
                    self.stdout.write("Aborted.")
                    return

        for graph in eligible_graphs:
            filterable_nodes = models.Node.objects.filter(
                graph=graph,
                datatype__in=FILTERABLE_DATATYPES,
                issearchable=True,
            ).order_by("name")

            config = {
                "nodes": [
                    {
                        "label": str(node.name),
                        "sortorder": index,
                        "node_alias": node.alias,
                        "filterable": False,
                        "sortable": False,
                    }
                    for index, node in enumerate(filterable_nodes, start=0)
                ]
            }

            if overwrite:
                _, created = NodeFilterConfig.objects.update_or_create(
                    graph=graph,
                    slug="filtering",
                    defaults={"config": config},
                )
                status = "Created" if created else "Overwritten"
            else:
                _, created = NodeFilterConfig.objects.get_or_create(
                    graph=graph,
                    slug="filtering",
                    defaults={"config": config},
                )
                status = "Created" if created else "Skipped"
            self.stdout.write(f"\t{status}: [filtering] on {graph.slug}")
