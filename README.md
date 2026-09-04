# Welcome to Arches Search!

Arches Search is an Arches application that replaces core search. It ships a Simple Search interface with per-graph attribute filters, an Advanced Search query builder, map-based (MVT) search, saved and shareable searches, and the indexes behind them.

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
        "arches_vue_components",
        "arches_controlled_lists",
        "arches_querysets",
    )
    ```

3. Next ensure arches and arches-search (along with its companion applications) are included as dependencies in package.json:

    ```
    "dependencies": {
        "arches": "archesproject/arches#dev/8.2.x",
        "arches-vue-components": "archesproject/arches-vue-components#dev/2.1.x",
        "arches-controlled-lists": "archesproject/arches-controlled-lists#dev/1.3.x",
        "arches-modular-reports": "archesproject/arches-modular-reports#2.1.x",
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

| Datatype    | Widget            | Behavior                                                                                             |
| ----------- | ----------------- | ---------------------------------------------------------------------------------------------------- |
| `number`    | `NumericFilter`   | Accepts discrete values and ranges (e.g. `9-10, 12`), OR-combined into `EQUALS` / `BETWEEN` clauses. |
| `reference` | `ReferenceFilter` | Lets the user pick one or more controlled-list values, combined into a `REFERENCES_ANY` clause.      |

A configured node whose datatype is not in the registry is returned by the API but isn't rendered as a filter. To support a new datatype, register one entry in `arches_search/src/arches_search/SimpleSearch/components/attribute-filters/registry.ts` (a widget component plus a `buildQuery` function) — no changes to the configuration format are required.

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

---

## Extending Advanced Search for a Custom Datatype

A custom datatype needs four things to work with Advanced Search:

1.  Registration with arches core, see [Registering your datatype](https://arches.readthedocs.io/en/stable/developing/extending/extensions/datatypes/#registering-your-datatype).
2.  `AdvancedSearchFacet` rows, added via a migration, pointing at whichever table fits: `TermSearch`, `UUIDSearch`, `DateSearch`, `NumericSearch`, `BooleanSearch`, `GeometrySearch`, `FileListSearch`.
3.  An indexer, so tile values get written into that table.
4.  Optionally, an operand normalizer, so values submitted from the UI are shaped correctly before comparison.

### Indexers

Subclass `arches_search.indexing.base.BaseIndexing`, point `self.datatype` at your datatype, and return the rows to write from `index(self, tile, node)`:

```python
from arches.app.datatypes.datatypes import DataTypeFactory
from arches_search.indexing.base import BaseIndexing
from arches_search.models.models import TermSearch


class MeasurementIndexing(BaseIndexing):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("measurement")

    def index(self, tile, node):
        raw_value = tile.data.get(str(node.nodeid))
        if not raw_value:
            return []
        return [
            TermSearch(
                node_alias=node.alias,
                tileid_id=tile.tileid,
                resourceinstanceid_id=tile.resourceinstance_id,
                datatype="measurement",
                graph_slug=node.graph.slug,
                value=raw_value["value"],
                language="",
            )
        ]
```

Declare `search_indexers` on your app's `AppConfig`:

```python
from django.apps import AppConfig


class MyAppConfig(AppConfig):
    search_indexers = [
        "my_app.indexing.MeasurementIndexing",
    ]
```

### Operand normalizers

Subclass `arches_search.utils.advanced_search.operand_normalization.base.BaseOperandNormalizer` and implement `normalize_value`. `operand_item["value"]` arrives in the same shape your datatype stores in a tile (a reference's list of `{"labels": [...]}` entries, a resource-instance's `{"resourceId": ...}`, etc.) — `normalize_value` turns that into whatever your facet's `orm_template` should actually compare against:

```python
from arches.app.datatypes.datatypes import DataTypeFactory
from arches_search.utils.advanced_search.operand_normalization.base import (
    BaseOperandNormalizer,
)


class MeasurementOperandNormalizer(BaseOperandNormalizer):
    def __init__(self):
        super().__init__()
        self.datatype = DataTypeFactory().get_instance("measurement")

    def normalize_value(self, operand_item):
        raw_value = operand_item.get("value")
        return raw_value.get("value") if isinstance(raw_value, dict) else raw_value

    def resolve_filter_value(self, operand_item):
        raw_value = operand_item.get("value")
        return raw_value.get("unit") if isinstance(raw_value, dict) else None
```

`resolve_filter_value` is only needed if your facet sets `filter_field` too (like `TermSearch`'s `language` column, or `unit` here). Whatever it returns gets compared against that column, and every operand in the same clause has to agree on the same value.

Declare `advanced_search_operand_normalizers` the same way, on the same `AppConfig`:

```python
class MyAppConfig(AppConfig):
    search_indexers = [
        "my_app.indexing.MeasurementIndexing",
    ]
    advanced_search_operand_normalizers = [
        "my_app.operand_normalization.MeasurementOperandNormalizer",
    ]
```

This is opt-in; a datatype with no normalizer just passes its value through untouched. Most scalar datatypes (numbers, booleans) don't need one at all.

## Clause Subjects

Every clause in an advanced search payload has the same five keys:

```json
{
    "type": "LITERAL",
    "quantifier": "ANY",
    "subject": { "...": "what is being matched" },
    "operator": "LIKE",
    "operands": [{ "type": "LITERAL", "value": "bronze" }]
}
```

The `subject` says _what_ is being matched. There are three kinds, and its
`type` tells them apart.

| Subject          | Matches                                           | Shape                                              |
| ---------------- | ------------------------------------------------- | -------------------------------------------------- |
| `NODE`           | one node's tile values, on one graph              | `graph_slug` + `node_alias`, empty `search_models` |
| `SEARCH_MODELS`  | any node of the named index classes, on one graph | `graph_slug` + `search_models`, empty `node_alias` |
| `RESOURCE_FIELD` | a column on the resource row itself               | `field`                                            |

The table compares their shapes; each example below is a whole clause, so it can
be lifted straight into `clauses`.

**`NODE`** is the common case — a named node on a named graph:

```json
{
    "type": "LITERAL",
    "quantifier": "ANY",
    "subject": {
        "type": "NODE",
        "graph_slug": "my_resource_graph",
        "node_alias": "material",
        "search_models": []
    },
    "operator": "LIKE",
    "operands": [{ "type": "LITERAL", "value": "bronze" }]
}
```

_Reads as:_ resources on `my_resource_graph` with a `material` value containing
"bronze". Returns those resources — not the matching tiles.

**`SEARCH_MODELS`** drops the node alias and names index classes instead, so one
clause can span every node of that kind on the graph — "any string field on a
Person contains X":

```json
{
    "type": "LITERAL",
    "quantifier": "ANY",
    "subject": {
        "type": "SEARCH_MODELS",
        "graph_slug": "person",
        "node_alias": "",
        "search_models": ["TermSearch"]
    },
    "operator": "LIKE",
    "operands": [{ "type": "LITERAL", "value": "CHARLIE" }]
}
```

_Reads as:_ People with "CHARLIE" in **any** of their string fields — first name,
nickname, whichever. You do not have to know which node it landed in.

Name more than one class to span them — `["DateSearch", "DateRangeSearch"]`
covers every time-ish node in one clause.

Drop the operands and it becomes a presence check: `HAS_ANY_VALUE` asks whether
the resource has any row of those classes at all, and `quantifier: "NONE"`
inverts it into "has none".

**`RESOURCE_FIELD`** addresses the resource row rather than its tiles, so it
names no graph and no node:

```json
{
    "type": "LITERAL",
    "quantifier": "ANY",
    "subject": { "type": "RESOURCE_FIELD", "field": "principaluser" },
    "operator": "IS_CURRENT_USER",
    "operands": []
}
```

_Reads as:_ resources created by whoever is asking. The empty `operands` is not
an omission: the requester is never named in the payload, so this clause means
something different for every caller and cannot be turned into a search for
somebody else. See [How many operands](#how-many-operands).

### What each one can do

The first two are reached with a correlated subquery against the denormalized
search tables, which is why they need a graph and why `quantifier` (`ANY` /
`ALL` / `NONE`) is meaningful: a node can hold many values across many tiles. A
resource field is a single column on the row already being filtered, so it
compiles to a plain predicate and its `quantifier` is ignored — send `ANY`.

That difference sets the rules:

-   **`RELATED` clauses require a `NODE` subject.** Traversal follows a node link.
-   **`RESOURCE_FIELD` is rejected under `TILE` scope.** There is no tile for it to
    be evaluated against, and a quietly ignored filter is worse than an error.
-   **Every group still names a graph.** A resource field clause carries no graph
    of its own, so the group it sits in decides which resource model it filters.
    A payload for `person` holding `IS_CURRENT_USER` narrows People, not
    everything — see [One payload per graph](#one-payload-per-graph).

Otherwise a `RESOURCE_FIELD` clause goes anywhere an ordinary clause goes. It
mixes with node clauses in one group, combines under the same `AND` / `OR`
logic, nests in subgroups, and works on **either side of a relationship**:

| Position                      |     |
| ----------------------------- | --- |
| Top-level group               | yes |
| Nested subgroup               | yes |
| `OR`-ed with a node clause    | yes |
| Anchor side of a relationship | yes |
| Child side of a relationship  | yes |
| `TILE` scope                  | no  |
| `RELATED` clause              | no  |

On a relationship, which side it constrains follows from where you put it —
in the traversing group it filters the anchor, in a subgroup under that group it
filters the related resource. So "people whose pet I own" is a resource field
clause on the child side, and "people I created who have any pet" is the same
clause on the anchor side.

```json
{
    "graph_slug": "person",
    "scope": "RESOURCE",
    "logic": "AND",
    "clauses": [
        {
            "type": "LITERAL",
            "quantifier": "ANY",
            "subject": {
                "type": "NODE",
                "graph_slug": "person",
                "node_alias": "last_name",
                "search_models": []
            },
            "operator": "LIKE",
            "operands": [{ "type": "LITERAL", "value": "rivera" }]
        },
        {
            "type": "LITERAL",
            "quantifier": "ANY",
            "subject": { "type": "RESOURCE_FIELD", "field": "principaluser" },
            "operator": "IS_CURRENT_USER",
            "operands": []
        }
    ],
    "groups": [],
    "aggregations": [],
    "relationship": null
}
```

_Reads as:_ People surnamed Rivera **that I created**. One clause reaches into a
tile, the other reads a column on the resource row, and `AND` applies to both the
same way.

### One payload per graph

`advanced_search_queries` is a **list**. Each entry is a complete advanced
search payload, and its `graph_slug` names the resource model that entry
returns.

`graph_slugs` chooses which resource models are searched. Within that set, a
graph an entry addresses is filtered by it; a graph no entry addresses is
returned whole. So you can ask for two resource models and refine only one:

```json
{
    "graph_slugs": ["person", "dog"],
    "advanced_search_queries": [
        {
            "graph_slug": "person",
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": "person",
                        "node_alias": "first_name",
                        "search_models": []
                    },
                    "operator": "EQUALS",
                    "operands": [{ "type": "LITERAL", "value": "FOO" }]
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": null
        }
    ]
}
```

People are narrowed to those named FOO; every Dog comes back, because nothing
addressed Dogs. Filtering both means a second entry with `"graph_slug": "dog"`.

Two things follow from that:

-   **A payload that matches nothing does not take other graphs with it.** If no
    Person is named FOO, the Dogs are still returned — they were requested, and
    nothing said anything about them.
-   **Each graph may be addressed once.** Two entries with the same `graph_slug`
    is a `400`, because silently applying one and ignoring the other is the worst
    available outcome.

To exclude a resource model entirely, leave it out of `graph_slugs`. That is the
selector; the payloads are the refinement.

**Selecting nothing returns nothing.** An absent or empty `graph_slugs` is not a
shorthand for "everything" — a caller has to name the resource models it wants:

```json
{
    "graph_slugs": [],
    "term_search": { "terms": ["amber"], "max_hops": 2 }
}
```

comes back with no resources. `resource_type_counts` and `all_resource_count`
still cover every active graph, though, so a client can show what naming one
would get. The resource type facet is built on exactly that.

### Validation

Shape is checked up front, without touching the database. Whether a field,
operator or node actually exists is settled as the query compiles, where the
registries are available. Either way you get a `400`, not a `500`.

Three rules govern an entry's `graph_slug`. Each one guards a way a search can
look like it worked when it didn't:

-   **It must be present and non-empty.** Without one there is no resource model
    for the entry to filter.
-   **It must name a real resource model.** A typo used to drop the entry
    without a word, and the graph it was meant to filter came back whole — a
    search that appears to have worked and quietly returns too much.
-   **Each graph may be addressed once**, as above: two entries for one graph is
    a `400` rather than one of them being ignored.

## Term search

`term_search` is the one filter that is not a clause, and the one that reaches
outside the graph being searched:

```json
"term_search": { "terms": ["amber"], "max_hops": 2 }
```

Terms are matched against every indexed text value on a resource (you never
name a node), then walked back across relationships, so a Site can be found
because its related Person is named Amber. All terms must match; each is
expanded independently and the results intersected, so a resource cannot qualify
by reaching two different terms down two unrelated paths.

`max_hops` is capped at 2, and `0` means "match directly, do not traverse".

**This is the only anonymous traversal in the API.** It follows any relationship,
in either direction, ignoring ontology properties — which is why it is not a
clause. A clause's `relationship` block is the opposite: a named node path, an
explicit `is_inverse`, and a quantifier. Do not read the two as variations of one
another, and do not call a clause's `relationship.path` segments "hops".

Everything else that filters a graph's own data is a clause. Geometry and date
filters used to sit beside `term_search` and are now ordinary `SEARCH_MODELS`
clauses:

```json
{
    "type": "LITERAL",
    "quantifier": "ANY",
    "subject": {
        "type": "SEARCH_MODELS",
        "graph_slug": "person",
        "node_alias": "",
        "search_models": ["DateSearch", "DateRangeSearch"]
    },
    "operator": "BETWEEN",
    "operands": [
        { "type": "LITERAL", "value": "1890-01-01" },
        { "type": "LITERAL", "value": "1910-01-01" }
    ]
}
```

_Reads as:_ resources with a date in that window, **or** a stored date range
overlapping it. Naming both models is what gets you the second half — each
resolves its own facet and the two OR together.

A `GEO_INTERSECTS` clause takes a whole GeoJSON `FeatureCollection` as a
`GEO_LITERAL` operand. Per-feature `buffer_distance` / `buffer_units` are applied
and the features unioned before the intersection, so a drawn area with a buffer
behaves the same as it did as a map filter.

**Composition.** `term_search` narrows each selected graph first, then that
graph's payload narrows what is left. They always `AND`, in that order — a term
search cannot be OR-ed against a clause or nested inside a group.

## Searching on Resource Fields

A `RESOURCE_FIELD` subject reaches the resource's own columns — its lifecycle
state, who created it, when it was made. Which fields exist is derived from
`ResourceInstance` itself, not from a hardcoded list: each concrete model field
is mapped to an operator vocabulary by its **Django field class**, so a column
added to core becomes filterable, sortable and groupable with no change here.
Fields whose class has no mapping (`name` and `descriptors`, both JSON-backed)
fall out automatically.

| Field class                   | Operators                                                             |
| ----------------------------- | --------------------------------------------------------------------- |
| `ForeignKey`                  | `EQUALS`, `IN`, `HAS_ANY_VALUE`, `HAS_NO_VALUE`                       |
| `UUIDField`                   | `EQUALS`, `IN`, `HAS_ANY_VALUE`, `HAS_NO_VALUE`                       |
| `DateTimeField` / `DateField` | `EQUALS`, `RANGE`, `BEFORE`, `AFTER`, `HAS_ANY_VALUE`, `HAS_NO_VALUE` |
| `CharField` / `TextField`     | `EQUALS`, `CONTAINS`, `STARTS_WITH`, `HAS_ANY_VALUE`, `HAS_NO_VALUE`  |
| `BooleanField`                | `IS_TRUE`, `IS_FALSE`                                                 |

A foreign key to the user model also gets `IS_CURRENT_USER` and
`IS_NOT_CURRENT_USER`, plus exactly one hop to that user's `username` — nothing
else on the user model is reachable.

### How many operands

An operator's operands are described by its facet row's `param_formats`, so the
count follows from the row rather than from a rule written here:

| Operators                                              | Operands                         |
| ------------------------------------------------------ | -------------------------------- |
| `HAS_ANY_VALUE`, `HAS_NO_VALUE`, `IS_TRUE`, `IS_FALSE` | none                             |
| `IS_CURRENT_USER`, `IS_NOT_CURRENT_USER`               | none — the server fills these in |
| `EQUALS`, `CONTAINS`, `STARTS_WITH`, `BEFORE`, `AFTER` | one                              |
| `IN`                                                   | one, holding a non-empty list    |
| `RANGE`                                                | two — lower bound, then upper    |

Sending an operand to a current-user operator is a `400`, not a silent no-op:
supplying one is an attempt to search as somebody else, and it should fail
loudly.

### Discovering the vocabulary

Fetch it rather than hardcoding it. `graph_slugs` is optional and scopes choice
lists such as lifecycle states, which differ per graph:

```
GET /api/advanced-search/resource-fields?graph_slugs=<slug>
```

## Search results

What a search carries back, and how it is ordered.

### Projecting additional data

`additional_data` asks for values to be carried on each result row. An entry
takes the same two shapes a clause subject does, and uses the same tokens:

```json
"additional_data": [
    { "type": "NODE", "graph_slug": "my_resource_graph", "node_alias": "height" },
    { "type": "RESOURCE_FIELD", "field": "resource_instance_lifecycle_state" }
]
```

A **`NODE`** entry annotates a node's value onto the row. The same annotation
backs both display and `ORDER BY`, so a value used for sorting and display costs
one annotation, not two.

A **`RESOURCE_FIELD`** entry carries the column's `value` **and** its `label`. A
result row already includes the resource's raw columns, so on its own it tells
you `resource_instance_lifecycle_state_id` is some UUID and nothing more; the
label is the word a reader wants. Both keys are always present, with a null
label for a field that names no related record (`createdtime`, `legacyid`).

The two kinds come back separately, because their names can collide: a node
aliased `principaluser` and the field of that name would otherwise fight over
one key.

They fail differently, and that is intentional. A node that does not resolve,
or whose nodegroup the requester cannot read, is **silently absent**: "no such
node", "not permitted" and "wrong graph" all look identical from outside. An
unqueryable resource field is a **400**: the registry is public (the metadata
endpoint serves it), so silence would hide a client's mistake while protecting
nothing.

### Example payload

`POST /api/search`

**In plain English:** _"Of my own records on `my_resource_graph`, show me the
bronze ones created in 2025 that are in one of these lifecycle states. Give me
each one's name, height and status, tallest first, twenty to a page."_

That single sentence is the whole payload below: `graph_slugs` picks the resource
model, the clauses narrow it (a tile value, the creator, the lifecycle state and
a date range, all `AND`-ed), `additional_data` says what to carry on each row,
and `sort` orders on one of them.

```json
{
    "graph_slugs": ["my_resource_graph"],
    "advanced_search_queries": [
        {
            "graph_slug": "my_resource_graph",
            "scope": "RESOURCE",
            "logic": "AND",
            "clauses": [
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "NODE",
                        "graph_slug": "my_resource_graph",
                        "node_alias": "material",
                        "search_models": []
                    },
                    "operator": "LIKE",
                    "operands": [{ "type": "LITERAL", "value": "bronze" }]
                },
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "RESOURCE_FIELD",
                        "field": "principaluser"
                    },
                    "operator": "IS_CURRENT_USER",
                    "operands": []
                },
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "RESOURCE_FIELD",
                        "field": "resource_instance_lifecycle_state"
                    },
                    "operator": "IN",
                    "operands": [
                        {
                            "type": "LITERAL",
                            "value": ["b2c3d4e5-0000-0000-0000-000000000000"]
                        }
                    ]
                },
                {
                    "type": "LITERAL",
                    "quantifier": "ANY",
                    "subject": {
                        "type": "RESOURCE_FIELD",
                        "field": "createdtime"
                    },
                    "operator": "RANGE",
                    "operands": [
                        { "type": "LITERAL", "value": "2025-01-01" },
                        { "type": "LITERAL", "value": "2025-12-31" }
                    ]
                }
            ],
            "groups": [],
            "aggregations": [],
            "relationship": null
        }
    ],
    "additional_data": [
        {
            "type": "NODE",
            "graph_slug": "my_resource_graph",
            "node_alias": "name"
        },
        {
            "type": "NODE",
            "graph_slug": "my_resource_graph",
            "node_alias": "height"
        },
        {
            "type": "RESOURCE_FIELD",
            "field": "resource_instance_lifecycle_state"
        }
    ],
    "sort": [
        {
            "type": "NODE",
            "graph_slug": "my_resource_graph",
            "node_alias": "height",
            "direction": "desc"
        }
    ],
    "page": 1,
    "page_size": 20
}
```

**What comes back:** the matching resources, each carrying the requested
columns, ordered by height descending — plus `pagination`, `resource_type_counts`
and `all_resource_count` alongside them.

Values are always a list, so a client never has to branch on cardinality:

```json
{
    "resources": [
        {
            "resourceinstanceid": "c3d4e5f6-0000-0000-0000-000000000000",
            "additional_data": {
                "node_values": {
                    "name": [
                        {
                            "node_value": "Bronze bowl",
                            "display_value": "Bronze bowl",
                            "details": []
                        }
                    ],
                    "height": [
                        {
                            "node_value": 12,
                            "display_value": "12",
                            "details": []
                        }
                    ]
                },
                "resource_fields": {
                    "resource_instance_lifecycle_state": {
                        "value": "b2c3d4e5-0000-0000-0000-000000000000",
                        "label": "Draft"
                    }
                }
            }
        }
    ],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total_results": 1,
        "num_pages": 1,
        "has_next": false,
        "has_previous": false
    }
}
```

### Sorting and grouping

`sort` is a list, applied in order:

| `type`           | Orders by                                                                 | Also needs                  |
| ---------------- | ------------------------------------------------------------------------- | --------------------------- |
| `primary_name`   | the resource's descriptor name in the active language, case-insensitively | —                           |
| `created_time`   | `createdtime`, the resource's creation timestamp                          | —                           |
| `NODE`           | a projected node (tile) value                                             | `graph_slug`, `node_alias`  |
| `RESOURCE_FIELD` | one of the resource's own columns                                         | `field`                     |

`NODE` and `RESOURCE_FIELD` are the same tokens a clause subject uses.
`primary_name` and `created_time` name no subject, so they stay lowercase.

Ordering by a node value annotates it for you; it does not have to appear in
`additional_data` as well. A node the requester may not read is skipped rather
than reported, matching how projection omits it.

Every sort is followed by a tie-break on `resourceinstanceid`, so paging stays
stable when the sort key ties. Foreign keys order by the related record's label
rather than its opaque primary key, and nulls sort last in both directions so a
nullable column does not lead on `desc`:

```json
{
    "sort": [
        {
            "type": "RESOURCE_FIELD",
            "field": "resource_instance_lifecycle_state",
            "direction": "asc"
        }
    ]
}
```

_Reads as:_ order by lifecycle state alphabetically by the state's **label**, so
"Draft" comes before "Submitted". Not by its UUID, which would be an arbitrary
order that changes whenever the data is reloaded.

`aggregations` accepts a `RESOURCE_FIELD` group-by for any field the registry
reports as groupable — foreign keys and booleans, the ones with bounded
cardinality. Grouping on something unbounded like `createdtime` is rejected:

```json
{
    "aggregations": [
        {
            "name": "by_state",
            "group_by": [
                {
                    "type": "RESOURCE_FIELD",
                    "field": "resource_instance_lifecycle_state",
                    "alias": "state"
                }
            ],
            "metrics": [
                {
                    "type": "RESOURCE_FIELD",
                    "alias": "total",
                    "fn": "Count",
                    "field": "resourceinstanceid"
                }
            ]
        }
    ]
}
```

_Reads as:_ "how many results are in each lifecycle state?" — the counts behind a
status facet.

Results come back keyed by the aggregation's `name`, each row carrying the
aliases you asked for:

```json
{ "by_state": [{ "state": "<uuid>", "total": 3 }] }
```

Three results in that state. The aggregation runs over the whole matching set,
not just the current page, so a facet count does not change as you page through.

### Permissions

A resource field clause narrows the candidate set and nothing more.
`permission_backend.filter_resource_queryset` runs unconditionally as the final
step, so no filter value can surface a resource the requester could not
otherwise see. `IS_CURRENT_USER` resolves server-side from the request user;
for an unauthenticated request it matches nothing rather than matching every
resource with no creator.

## Other endpoints

These share the filtering vocabulary of `POST /api/search`, so anything you can
express there works here too.

### Export

`POST /api/search-export` takes the same filtering payload and returns an
`.xlsx` instead of JSON. Two extra keys: `filename` (default `search_export`,
`.xlsx` appended if missing) and `allDescriptors` — when true the export carries
every language rather than the active one.

It runs the same `validate_search_payload` the search does, so an export cannot
quietly cover a different set than the search it came from. `additional_data`,
`sort` and `page` are ignored: an export is the whole matching set.

### Map tiles

Tiles come in two steps, because a tile response is protobuf and has nowhere to
report a bad payload:

```
POST /api/arches-search/mvt-context                          -> { "context_id": "<uuid>" }
GET  /api/arches-search/mvt/{context_id}/{zoom}/{x}/{y}.pbf
```

The context call validates the payload and caches it under a fresh id. Every
tile after that reads the cached payload, so a malformed search fails once, as a
`400` with a readable body, instead of as blank tiles. Tiles are cached per
context, user and coordinate.

### Saved searches

```
GET    /api/saved-searches?scope=mine|shared&search=<text>
POST   /api/saved-searches
DELETE /api/saved-searches/{savedsearchid}
```

`scope` defaults to `mine`; `shared` lists searches shared with the requester
by user or by group.

### Term suggestions

`GET /api/term-suggestions?q=<text>` — the typeahead behind the search bar,
returning the indexed terms a query prefix matches.
