# Welcome to Arches Search!

Arches Search is an Arches application that provides a modern, configurable search experience for Arches. It ships a Simple Search interface with per-graph attribute filters, an Advanced Search query builder, map-based (MVT) search, saved and shareable searches, and supporting search indexes.

Please see the [project page](http://archesproject.org/) for more information on the Arches project.

## Installation

If you are installing Arches Search for the first time, **we strongly recommend** that you install it as an Arches application into an existing (or new) project. Running Arches Search as a standalone project can provide some convenience if you are a developer contributing to the Arches Search project, but you risk conflicts when upgrading to the next version of Arches Search.

### If installing for development

Clone the arches-search repo and check out the latest `dev/x.x.x` branch (or any other branch you may be interested in). Navigate to the `arches-search` directory from your terminal and run the following commands:

```
pip install -e . --group dev
pre-commit install
```

`Important`: Installing the arches-search app will install Arches as a dependency. This may replace your current install of Arches with a version from PyPI. If you've installed Arches for development using the `--editable` flag, you'll need to reinstall Arches using the `--editable` flag again after installing arches-search.

### If installing for deployment, run:

```
pip install arches-search
```

## Project Configuration

1. If you don't already have an Arches project, you'll need to create one by following the instructions in the Arches [documentation](http://archesproject.org/documentation/).

2. When your project is ready, add `arches_search` and its companion applications to INSTALLED_APPS **below** the name of your project. `arches_search` ships templates (`index.htm`, `arches_urls.htm`, the custom email templates, etc.) that override arches core, so it must be listed **above** core arches — which is why core (`arches.app`) is added last, after all applications:

    ```
    INSTALLED_APPS = (
        ...
        "my_project_name",
        "arches_search",
        "arches_modular_reports",
        "arches_component_lab",
        "arches_controlled_lists",
        "arches_querysets",
    )
    ```

3. Next ensure arches and arches-search (along with its companion applications) are included as dependencies in package.json:

    ```
    "dependencies": {
        "arches": "archesproject/arches#dev/8.1.x",
        "arches-component-lab": "archesproject/arches-component-lab#main",
        "arches-controlled-lists": "archesproject/arches-controlled-lists#dev/1.1.x",
        "arches-modular-reports": "archesproject/arches-modular-reports#main",
        "arches-search": "archesproject/arches-search#main"
    }
    ```

4. Update urls.py to include the arches_search urls:

    ```
    urlpatterns = [
        ...
    ]

    urlpatterns.append(path("", include("arches_search.urls")))

    # Ensure Arches core urls are superseded by project-level urls
    urlpatterns.append(path("", include("arches.urls")))
    ```

5. Run migrations:

    ```
    python manage.py migrate
    ```

6. Start your project:

    ```
    python manage.py runserver
    ```

7. Next cd into your project's app directory (the one with package.json) and install and build the front-end dependencies:

    ```
    npm install
    npm run build_development
    ```

## Developer Setup (for contributing to the Arches Search project)

1. Download the arches-search repo:

    a. If using the [Github CLI](https://cli.github.com/): `gh repo clone archesproject/arches-search`

    b. If not using the Github CLI: `git clone https://github.com/archesproject/arches-search.git`

2. Download the arches package:

    a. If using the [Github CLI](https://cli.github.com/): `gh repo clone archesproject/arches`

    b. If not using the Github CLI: `git clone https://github.com/archesproject/arches.git`

3. Create a virtual environment outside of both repositories:
    ```
    python3 -m venv ENV
    ```

4. Activate the virtual environment in your terminal:
    ```
    source ENV/bin/activate
    ```

5. Navigate to the `arches-search` directory, and install the project (with development dependencies):
    ```
    cd arches-search
    pip install -e . --group dev
    ```

6. Also install core arches for local development:
    ```
    pip install -e ../arches
    ```

7. Install the pre-commit hooks:
    ```
    pre-commit install
    ```

8. Run the Django server:
    ```
    python manage.py runserver
    ```

9. (From the `arches-search` top-level directory) install the frontend dependencies:
    ```
    npm install
    ```

10. Once the dependencies have been installed, generate the static asset bundle:

    a. If you're planning on editing HTML/CSS/JavaScript files, run `npm start`. This will start a development server that will automatically detect changes to static assets and rebuild the bundle.

    b. If you're not planning on editing HTML/CSS/JavaScript files, run `npm run build_development`

11. Setup the database:
    ```
    python manage.py setup_db
    ```

12. In the terminal window that is running the Django server, halt the server and restart it.
    ```
    (ctrl+c to halt the server)
    python manage.py runserver
    ```

---

## Configuring Attribute Filters

The Simple Search interface can present a set of **attribute filters** — per-node filter widgets (for example, a numeric range input or a controlled-list reference picker) that let users narrow results by the values of specific nodes on a graph.

Which nodes appear as filters, in what order, and under what labels is controlled per graph by a `NodeFilterConfig` record. There is no dedicated UI for editing these yet, so they are created through the [Django admin](https://arches.readthedocs.io/en/stable/administering/django-admin-ui/) or a data migration.

### The configuration record

A `NodeFilterConfig` has three meaningful fields:

-   **`graph`** — the resource graph these filters apply to.
-   **`slug`** — a name that distinguishes multiple filter configurations for the same graph. It defaults to `"filtering"`, which is the configuration Simple Search loads by default.
-   **`config`** — a JSON object whose only key is `"nodes"`, a list of the nodes to expose as filters.

### Structure of `config`

```json
{
    "nodes": [
        {
            "node_alias": "height",
            "label": "Height (cm)",
            "sortorder": 1
        },
        {
            "node_alias": "material",
            "label": "Material",
            "sortorder": 2
        },
        {
            "node_alias": "name"
        }
    ]
}
```

Each entry in the `nodes` array describes one filter:

#### `node_alias`

-   **Type:** `string` (required)
-   **Description:** The alias of the node on the graph to expose as a filter. Entries whose alias does not resolve to a node on the graph are silently skipped, as are nodes the requesting user does not have permission to read.

#### `label`

-   **Type:** `string` (optional)
-   **Description:** The label shown above the filter widget. If omitted, the node's own name is used.

#### `sortorder`

-   **Type:** `integer` (optional)
-   **Description:** Controls the order in which filters are displayed, ascending. Defaults to `0`.

### How a node becomes a widget

When Simple Search loads, it requests the configuration for the active graph from:

```
GET /api/advanced-search/graph/<graph_id>/search-config?slug=filtering
```

The API resolves each configured alias to a concrete node and returns its `datatype` (along with the node's id, nodegroup id, resolved label, sortorder, and node config). On the front end, the node's datatype is looked up in the attribute-filter **registry**, which maps a datatype to the widget that renders it and the function that turns the widget's value into a search query. Out of the box the registry supports:

| Datatype    | Widget            | Behavior                                                                                            |
| ----------- | ----------------- | --------------------------------------------------------------------------------------------------- |
| `number`    | `NumericFilter`   | Accepts discrete values and ranges (e.g. `9-10, 12`), OR-combined into `EQUALS` / `BETWEEN` clauses. |
| `reference` | `ReferenceFilter` | Lets the user pick one or more controlled-list values, combined into a `REFERENCES_ANY` clause.      |

A configured node whose datatype is not in the registry is returned by the API but simply isn't rendered as a filter. To support a new datatype, register one entry in `arches_search/src/arches_search/SimpleSearch/components/attribute-filters/registry.ts` (a widget component plus a `buildQuery` function) — no changes to the configuration format are required.

### Example: creating a config in a data migration

```python
from django.db import migrations


def add_filter_config(apps, schema_editor):
    GraphModel = apps.get_model("models", "GraphModel")
    NodeFilterConfig = apps.get_model("arches_search", "NodeFilterConfig")

    graph = GraphModel.objects.get(slug="my_resource_graph")
    NodeFilterConfig.objects.create(
        graph=graph,
        slug="filtering",
        config={
            "nodes": [
                {"node_alias": "height", "label": "Height (cm)", "sortorder": 1},
                {"node_alias": "material", "label": "Material", "sortorder": 2},
            ]
        },
    )


class Migration(migrations.Migration):
    dependencies = []
    operations = [migrations.RunPython(add_filter_config, migrations.RunPython.noop)]
```

In this example `height` is a `number` node, so it renders as a numeric range/value input, and `material` is a `reference` node, so it renders as a controlled-list picker.
