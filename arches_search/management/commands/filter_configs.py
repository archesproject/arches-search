import glob
import json
import os
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from arches.app.models import models
from arches.app.models.system_settings import settings

from arches_search.models.models import NodeFilterConfig

CONFIGURABLE_DATATYPES = ("number", "reference")


class Command(BaseCommand):
    """
    Commands for managing node filter configurations

    """

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=["load", "write", "generate"],
            help='"load", "write", or "generate" (create filter configs for all the graphs).',
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
            "-s",
            "--source",
            action="store",
            dest="source",
            help="Source location of filter configs",
        )

        parser.add_argument(
            "-d",
            "--dest",
            action="store",
            dest="dest",
            help="Destination location of filter configs",
        )

        parser.add_argument(
            "--slug",
            action="store",
            dest="slug",
            default=None,
            help="Filter config slug to operate on (write operation only). Defaults to all slugs.",
        )

        parser.add_argument(
            "--overwrite",
            action="store_true",
            dest="overwrite",
            default=False,
            help="Generate filter configs",
        )

    def handle(self, *args, **options):
        graph_slug = options["graph"]

        if options["operation"] == "load":
            if options["source"]:
                self.load_filter_configs(options["source"], graph_slug=graph_slug)
            elif os.path.exists(os.path.join(settings.APP_ROOT, "filter_configs")):
                source = os.path.join(settings.APP_ROOT, "filter_configs/**")
                self.load_filter_configs(source, graph_slug=graph_slug)

        elif options["operation"] == "write":
            if options["dest"]:
                self.write_filter_configs(
                    options["dest"], slug=options["slug"], graph_slug=graph_slug
                )
            elif os.path.exists(os.path.join(settings.APP_ROOT, "filter_configs")):
                dest = os.path.join(settings.APP_ROOT, "filter_configs")
                self.write_filter_configs(
                    dest=dest, slug=options["slug"], graph_slug=graph_slug
                )

        elif options["operation"] == "generate":
            self.generate_filter_configs(
                graph_slug=graph_slug,
                overwrite=options["overwrite"],
            )

    def write_filter_configs(self, dest, slug=None, graph_slug=None):
        configs = NodeFilterConfig.objects.select_related("graph")
        if slug:
            configs = configs.filter(slug=slug)
        if graph_slug and graph_slug != "all":
            configs = configs.filter(graph__slug=graph_slug)
        for config in configs:
            os.makedirs(os.path.join(dest, config.graph.slug), exist_ok=True)
            file_path = os.path.join(dest, config.graph.slug, f"{config.slug}.json")
            with open(file_path, "w") as f:
                json.dump(config.config, f, indent=2)
            self.stdout.write(f"\tWritten: [{config.slug}] on {config.graph.slug}")

    def load_filter_configs(self, configs_dir, graph_slug=None):
        config_dirs = glob.glob(configs_dir)
        for config_dir in config_dirs:
            dir_graph_slug = Path(config_dir).stem
            if graph_slug and graph_slug != "all" and dir_graph_slug != graph_slug:
                continue
            for file in glob.glob(os.path.join(config_dir, "*.json")):
                with open(file) as f:
                    data = json.load(f)
                try:
                    graph = models.GraphModel.objects.get(slug=dir_graph_slug)
                except ObjectDoesNotExist as e:
                    self.stderr.write(
                        self.style.ERROR(
                            f"\tFilter config at {file} failed to save and was not loaded.\n\tErrors: {e}"
                        )
                    )
                    continue
                NodeFilterConfig.objects.update_or_create(
                    graph=graph,
                    slug=Path(file).stem,
                    defaults={"config": data},
                )
                self.stdout.write(
                    f'\tLoaded: [{Path(file).stem}] on graph "{dir_graph_slug}"'
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
            filterable_nodes = (
                models.Node.objects.filter(
                    graph=graph,
                    datatype__in=CONFIGURABLE_DATATYPES,
                    issearchable=True,
                    nodegroup__isnull=False,
                    nodegroup__parentnodegroup__isnull=True,
                    cardxnodexwidget__visible=True,
                )
                .distinct()
                .prefetch_related(
                    Prefetch(
                        "cardxnodexwidget_set",
                        queryset=models.CardXNodeXWidget.objects.filter(visible=True)
                        .select_related("card")
                        .order_by("card__sortorder", "sortorder"),
                    )
                )
            )
            filterable_nodes = sorted(filterable_nodes, key=self.get_sort_key)

            config = {
                "nodes": [
                    {
                        "label": self.get_widget_label(node),
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

    def get_sort_key(self, node):
        card_node_widget = node.cardxnodexwidget_set.all()[0]
        card_sortorder = card_node_widget.card.sortorder
        widget_sortorder = card_node_widget.sortorder
        return (
            card_sortorder is None,
            card_sortorder or 0,
            widget_sortorder is None,
            widget_sortorder or 0,
            str(node.name),
        )

    def get_widget_label(self, node):
        card_node_widgets = list(node.cardxnodexwidget_set.all())
        if card_node_widgets and card_node_widgets[0].label:
            widget_label = str(card_node_widgets[0].label).strip()
            if widget_label:
                return widget_label
        return str(node.name)
