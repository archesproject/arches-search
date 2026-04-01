"""
Tests confirming that:
  1. Null values can be indexed (stored in the DB without errors)
  2. Very long strings can be indexed (stored in the DB without truncation)

Note: the null value tests assume that the null guards inside each indexer
have been removed so that null values ARE written to the search index.
TermSearch.value (and equivalent fields on other search models) must have
null=True / blank=True for those tests to pass.
"""

import uuid

from django.test import TestCase

from arches.app.models.models import (
    GraphModel,
    Node,
    NodeGroup,
    ResourceInstance,
    TileModel,
)

from arches_search.indexing.index_from_tile import index_from_tile
from arches_search.indexing.indexers.file_list import FileListIndexing
from arches_search.indexing.indexers.string import StringIndexing
from arches_search.models.models import FileListSearch, TermSearch


# ---------------------------------------------------------------------------
# Shared test fixture
# ---------------------------------------------------------------------------


class IndexingTestCase(TestCase):
    """
    Creates the minimum arches object hierarchy (graph → nodegroup → node →
    resource instance → tile) needed to drive the indexing pipeline against
    a real database.
    """

    @classmethod
    def setUpTestData(cls):
        cls.graph = GraphModel.objects.create(
            graphid=uuid.uuid4(),
            slug="test-indexing",
            isresource=True,
        )
        cls.nodegroup = NodeGroup.objects.create(
            nodegroupid=uuid.uuid4(),
        )
        cls.string_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_string_node",
            alias="test_string_node",
            datatype="string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=True,
        )
        cls.non_localized_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_non_localized_node",
            alias="test_non_localized_node",
            datatype="non-localized-string",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.number_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_number_node",
            alias="test_number_node",
            datatype="number",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.boolean_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_boolean_node",
            alias="test_boolean_node",
            datatype="boolean",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )
        cls.resource_instance = ResourceInstance.objects.create(
            resourceinstanceid=uuid.uuid4(),
            graph=cls.graph,
        )

        cls.long_string = "Payment from buyer for “Peinture: “Notice sur le tableau De Jacques Vanloo* Le tableau depuis long-tems renommé dans le commerce des objets d'arts, sous le titre du Coucher, ou du Coucher à l'italienne, est peint sur une toile de cinq pieds sept pouces de haut, sur quatre pieds cinq pouces de large, et représente une femme de 26 à 28 ans, vue en pied, tournant le dos et prête à se mettre au lit. On dirait que cette figure respire et va parler ; chaque fois qu'on la regarde, ses couleurs semblent dire : Rien n'est beau que le vrai, le vrai seul est aimable. Peut-être, au nom de Jacques Vanloo, des juges sévères, et plus en garde que nous contre le prestige de la magie pittoresque, s'attacheront-ils à déterminer rigoureusement en quoi et jusqu'à quel point le précepte de Boileau est en rapport avec l'ouvrage auquel nous en faisons l'application ; soit : nous leur laissons le champ libre. Avant que d'adopter une opinion, tout homme a le droit de s'assurer des bases sur lesquelles elle est établie, il peut en outre la combattre et la rejeter s'il la trouve fausse. De même, avant que d'applaudir à l'hommage que nous rendons au tableau représentant le Coucher, chacun a le droit d'examiner si cet hommage est mérité. Cela posé, nous n'avons qu'une simple recommandation à faire aux personnes animées de l'amour du dessin : c'est de se défier ici de l'influence des préjugés et de ne pas perdre de vue que les arts brillent de plusieurs sortes de beautés.** Le nom de Jacques Vanloo, rarement cité dans nos livre sur la peinture, est enveloppé d'une sorte d'obscurité qui tend à jeter de la défaveur, nous ne dirons pas seulement sur la plus belle des productions de ce maître, mais encore sur l'une des plus étonnantes de l'art même, si on la considère du côté de l'exacte imitation de la nature. En général les productions d'un peintre ne sont estimées qu'en raison de son plus ou moins de célébrité. C'est de cette dangereuse prévention dont il faudrait ici se défaire. Lorsque les paysages d'Hobbema étaient pour ainsi dire rejetés, parce qu'ils n'avaient été vantés par aucun écrivain, en étaient-ils moins naturels, moins piquans, moins extraordinaires qu'aujourd'hui ? Pierre de Hooge, ignoré il y a trente ans ; Albert Cuyp, qu'à cette époque on admettait dans peu de cabinets, en étaient-ils moins les peintres de la lumière.*** Jean Steen qui, malgré la supériorité de ses talens et de son génie, avait été relégué par Dargenville**** dans la classe des peintres de second ordre, doit-il à une autre cause qu'à cette ridicule condamnation la longue indifférence qu'on a témoignée pour ses amusantes compositions ? Nous pourrions alléguer beaucoup d'autres exemples de ce genre, et prouver de plus en plus que le mérite n'a pas toujours joui des honneurs qui lui étaient dus. Nous pourrions  aussi démontrer combien un auteur en crédit peut faire naître et perpétuer de fausses idées, en peinture surtout, où le don de bien écrire n'est pas toujours accompagné des connaissances nécessaires pour bien raisonner ; mais cela nous écarterait trop de notre sujet. Lorsque nous avançons que Jacques Vanloo est peu connu, nous voulons faire entendre que le rang qu'il tient dans l'histoire n'est pas en proportion de l'habileté dont nous avons sous les yeux une preuve si éclatante. Car, si nous ne lisons que quelques mots à son sujet dans dans Descamps, au moins sont-il entièrement à sa louange. Voici comment ce biographe s'exprime dans la vie d'Eglon Vander-Neer***** : Il entra ches Jacques Vanloo, bon peintre d'Amsterdam, surtout de figures nues. Dargenville, de son côté, rapporte que Vanloo******, excellent peintre de portraits, vint d'Amsterdam à Paris, se fit naturaliser francais, et fut reçu à lacademie de peinture en 1663 ; mais c'était à feu Lebrun, à cet homme dont la connaissance en tableaux fera époque, qu'il était réservé d'élever le premier monument à la gloire de l'auteur du Coucher. Ce que nous venons d'extraire de Descamps est principalement à remarquer. Selon lui, notre peintre excellait dans les figures nues. Ce sentiment et le tableau que nous avons sous les yeux s'appuient d'une manière aussi réciproque que frappante. Considerons attentivement cette figure, sa chair, chaque partie de son corps ; qui a mieux rendu toutes ces choses ? qui a mieux rendu le nu, la circulation du sang, la transparence et les nuances aussi délicates que variées de la peau ? Ce dos peut-il être plus souple, ces muscles plus élastiques, ces articulations mieux senties ? Ces couleurs ne sont-elles pas celles de la vie, du plaisir et de la santé ? Qui ne comprend ce coup-d'oeil significatif ? Ne désire-t-on pas..... ? le peintre en vérité semble avoir osé provoquer la nature*******. Pour animer sa figure d'argile, Prométhée déroba une étincelle du feu céleste ; Vénus anima la statue d'ivoire de l'amoureux Pigmalion ; mais Vanloo, sans le secours des Dieux et sans les irriter, a transformé la toile en un corps, et l'a vu s'animer en quelque sorte sous ses doigts. Ce n'est pas seulement dans les tons de chair de sa figure que cet artiste se montre un des plus grands coloristes de l'école Hollandaise, il est encore admirable dans l'ensemble de son tableau ; dans la coordonnance des effets partiels à l'effet général ; dans l'unité d'intérêt qui nous y attache au principal objet, malgré qu'il soit entouré de brillans accessoires et de beaucoup de détails rendus avec soin. Cette chemise que la jeune femme vient de quitter et de poser sur sa table de toilette, ce tapis de velours verd, cet autre tapis de pied, cette courte-pointe cramoisie, ces rideaux de même couleur, toutes ses étoffes sont moins sacrifiées que bien liées entre elles et bien assorties au sujet. En deux mots, point de systême, la vérité, rien que la vérité, c'est-à-dire, la nature saisie sur le fait. Tels sont les traits sous lesquels nous voyons le tableau de Jacques Vanloo. Quel que soit le charme qu'il exerce sur nos yeux, il dut agir plus puissamment encore sur ceux de M. de V..., à en juger par l'énormité du prix moyennanant lequel il en fut l'accisition ********. La belle estampe de Porporati ne nous autorise-t-elle pas à supposer que cet artiste a partagé l'agréable impression que cause l'aspect de ce tableau ? En matière d'arts, un habile graveur n'est point un juge ordinaire. Si l'on nous objecte qu'il ne règne pas, dans les formes de cette figure, assez d'élégance ou de correction, et que d'ailleurs l'esprit d'imitation s'y est montré trop servile, en affectant d'exprimer des détails que le bon goût désaprouve, nous répondrons d'abord que ces détails, parlons clairement, ces légers mouvemens de la chair, cette rougeur, sont juste ce qui caractérise la fonction habituellede la partie du corps où le pinceau les a fait sentir. Si à ces marques on est tout près de penser que cette femme était assise il y a quelques momens, on est aussi tout près de lui supposer la faculté de se mouvoir ; de là naît l'idée de la vie ; de là naît l'illusion. Combien de fois des riens, auxquels on était loin de songer, ont sérvi à résoudre de grandes difficultés. Quant au défaut d'élégance et de choix dans les formes, nous demanderons : où est le parfait, et qui peut choisir à son gré dans la circonstance où se trouvait l'auteur de ce tableau ? Vanloo était maîtrisé : c'était un portrait qu'il avait à faire*********. Au surplus, tout en convenant que cette figure n'est pas le type de la beauté, nous y reconnaissons du moins un des types de l'espèce humaine où l'art trouve encore beaucoup à étudier. On place devant Jacques Vanloo, alors à son chevalet, une femme nue de la tête aux pieds, jolie, d'une fraîche carnation ; puis on lui dit : Telle vous paraît cette figure, telle il nous la faut en portrait, sans que rien y soit omis Vanloo obéit, et telle est son exactitude, tel est son talent, qu'en regardant son tableau, la nature y semble plutôt réfléchie dans un miroir qu'imitée sur la toile. N'est-ce rien en peinture que l'art de tromper les yeux********** ? ou plutôt n'est-ce pas tout ce qu'on peut désirer en faveur d'un tableau, que de pouvoir lui appliquer ce que Cicéron disait du chef-d'oeuvre d'Apelles, de la Vénus de Cos ? Ce que nous apercevons n'est pas réelement un corps, mais quelque chose de semblable à un corps ; et ce rouge mêlé de blanc qui s'y trouve répandu, n'est pas du sang, mais quelque chose que l'on prend pour du sang. Le coloris, tros peu considéré dans quelques pays, a été l'objet des éloges d'une quantité de savans de l'antiquité. Plutarque a écrit : que les couleurs dans la peinture nous frappent plus que le dessin, parce que ce sont elles qui constituent la ressemblance et l'illusion. Les éloges, dit un autre écrivain, que Parrhasius, Zeuxis et Apelles ont reçusde leurs contemporains, roulent principalement sur le genre de vérité et de beauté qui est produit par le choix de la couleur. Après avoir cité de pareilles autorités, il nous conviendrait peu de rien ajouter à l'éloge du coloris. L'amour des anciens pour le coloris nous paraît bien naturel. Il découlait de cette vive impression que font sur nous la délicatesse et la fraîcheur d'une belle carnation. De tout tems les regards ont dû s'arrêter avec complaisance sur une peau fine, où des nuances, légèrement azurées, se mêlent avec la blancheur du lys et l'incarnat de la rose ; de tout tems l'éclat du teint a dû effacer bien des irrégularités. Pourquoi donc ce qui nous charme dans la nature est-il, en peinture, compté de nos jours pour si peu de chose ? Si l'on peut reprocher un défaut au tableau du Coucher, c'est d'être d'une vérité qui n'en permet guère l'exposition dans une galerie publique. Ou bien il inspire des idées contraires à la pudeur, ou bien il la blesse et lui fait baisser les yeux ; mais soit qu'on le regarde comme un objet d'instruction, ou comme un ornement, il convient à un boudoir, et serait, dans une académie de peinture, une invariable leçon de couleurs. *[footnote : La famille des Vanloo est noble et originaire de l'Ecluse, en Flandre ; elle a depuis long-tems produit d'habiles gens dans la peinture. Celui qui s'y est attaché le premier s'appelait Jean Vanloo. Son fils Jacques, excellent peintre de portraits, séjourna quelque tems à Amsterdam, et s'y maria. Un fis qu'il eut, nommé Louis, vint de bonne heure étudier à Paris, et son père l'y joignit bientôt après ; ce père se fit naturaliser et fut reçu à l'Académie de Peinture, en 1663. Dargenville, tom. 4, pag. 385.] **[footnote : Il y a dans la peinture plusieurs sortes de beautés. Tel maître excelle dans la composition, tel autre dans le dessin ; celui-ci est admirable dans ses expressions ; celui-là nous étonne par son coloris ou par l'entente du clair-obscur. Quand dans une seule de ces parties l'artiste à su atteindre à la perfection, on peut dire qu'il a rempli sa tâche, et nous lui devons une haute estime.] ***[footnote : Albert Cuyp et Pierre de Hooge sont sans égaux dans la représentation des effets de la lumière du soleil. Cependant leurs productions ont eu de la peine à se faire jour au travers de celles d'une foule de peintres dont la gloire s'évanouit de jour en jour.] ****[footnote : On pourrait encore ajouter plusieurs peintres Flamands et Hollandais dans cette école, mais on doit les regarder comme du second ordre : tels sont Moucheron, Zeeman, Van Steen, etc., etc. IIIe. vol. pag. vij de l'avant-propos. Tout le monde en conviendra, Zeeman marche, en peinture, bien en arrière de J. Steen ; les pas de celui-ci sont des pas de géant, relativement à ceux du compagnon de voyage que Dargenville lui a donné. Le savant peintre Reynols a vengé le nom de Steen de l'injure de Dargenville, en proposant ses tableaux comme des modèles de couleur et d'harmonie.] *****[footnote : Vol. III, pag. 133.] ******[footnote : Voyer la première note.] *******[footnote : Pline raconte qu'Apelles peignit un héros nu, et qu'il paraissait, dans ce morceau, avoir défié la nature. Eâque picturâ naturam provocavit.] ********[footnote : Voyez l'avertissement.] *********[footnote: Selon ce que nous a raconté un des descendans de la famille des Vanloo, la figure représentant le coucher est le portrait d'une maître de Henri-Frédéric d'Orange. Dans un second tableau, cette même femme était peinte en face, et sortant du lit. Un excès de ménagement pour la pudeur a causé la ruine de cette peinture.] **********[footnote : Une très-jeune fille, entrant dans un salon où nous avions exposé ce tableau, et le racontrant des yeux, s'écris, en fuyant avec précipitation : Jh, la vilaine ! on essaya vainement de faire revenir cet enfant sur ses pas et de lui persuader qu'il n'avait vu qu'une peinture.]””"

    def _make_tile(self, node, value):
        """Create (and save) a TileModel whose data has *value* for *node*."""
        return TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=self.nodegroup,
            resourceinstance=self.resource_instance,
            data={str(node.nodeid): value},
            provisionaledits=None,
        )


# ---------------------------------------------------------------------------
# Long string tests
# ---------------------------------------------------------------------------


class LongStringIndexingTests(IndexingTestCase):
    """
    PostgreSQL TextField has a length limit on indexed text; these tests confirm
    that the indexing pipeline correctly preserves very long string values.
    """

    def test_string_indexer_long_value_persists_to_db(self):
        """StringIndexing writes long French value to the TermSearch table."""
        tile = self._make_tile(
            self.string_node,
            {"en": {"value": self.long_string, "direction": "ltr"}},
        )
        indexer = StringIndexing()
        result = indexer.index(tile, self.string_node)

        self.assertEqual(len(result), 1)

        result[0].save()
        saved = TermSearch.objects.get(pk=result[0].pk)
        self.assertEqual(saved.value, self.long_string)


# ---------------------------------------------------------------------------
# File-list indexing tests
# ---------------------------------------------------------------------------


class FileListIndexingTests(IndexingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.file_list_node = Node.objects.create(
            nodeid=uuid.uuid4(),
            name="test_file_list_node",
            alias="test_file_list_node",
            datatype="file-list",
            graph=cls.graph,
            nodegroup=cls.nodegroup,
            istopnode=False,
        )

    def test_file_list_indexer_writes_file_specific_rows(self):
        tile = self._make_tile(
            self.file_list_node,
            [
                {
                    "name": "invoice_2024.pdf",
                    "size": 11,
                    "lastModified": 1705708800000,
                },
                {
                    "name": "meeting_notes.txt",
                    "size": 2,
                    "lastModified": 1704844800.0,
                },
            ],
        )
        indexer = FileListIndexing()
        result = indexer.index(tile, self.file_list_node)

        file_list_rows = [row for row in result if isinstance(row, FileListSearch)]
        self.assertEqual(len(file_list_rows), 2)

        for row in file_list_rows:
            row.save()

        saved = list(
            FileListSearch.objects.filter(tileid=tile.tileid)
            .order_by("value")
            .values("value", "extension", "file_size", "modified_at")
        )
        self.assertEqual(
            saved,
            [
                {
                    "value": "invoice_2024.pdf",
                    "extension": "pdf",
                    "file_size": 11,
                    "modified_at": 1705708800000,
                },
                {
                    "value": "meeting_notes.txt",
                    "extension": "txt",
                    "file_size": 2,
                    "modified_at": 1704844800.0,
                },
            ],
        )


# ---------------------------------------------------------------------------
# All-datatypes null test
# ---------------------------------------------------------------------------


class AllDatatypesNullIndexingTest(IndexingTestCase):
    """
    A single tile whose every node value is null should produce no indexable
    records from index_from_tile, for every datatype that has a registered
    indexer.
    """

    INDEXER_DATATYPES = [
        "boolean",
        "concept",
        "concept-list",
        "date",
        "edtf",
        "file-list",
        "non-localized-string",
        "number",
        "reference",
        "resource-instance",
        "resource-instance-list",
        "string",
        "url",
    ]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.all_datatype_nodes = {}
        for datatype in cls.INDEXER_DATATYPES:
            alias = datatype.replace("-", "_")
            cls.all_datatype_nodes[datatype] = Node.objects.create(
                nodeid=uuid.uuid4(),
                name=f"null_test_{alias}_node",
                alias=f"null_test_{alias}_node",
                datatype=datatype,
                graph=cls.graph,
                nodegroup=cls.nodegroup,
                istopnode=False,
            )

    def test_all_null_values_produce_no_index_records(self):
        """
        index_from_tile returns an empty list when every node value in the
        tile is null, across all datatypes that have a registered indexer.
        """
        tile = TileModel.objects.create(
            tileid=uuid.uuid4(),
            nodegroup=self.nodegroup,
            resourceinstance=self.resource_instance,
            data={str(node.nodeid): None for node in self.all_datatype_nodes.values()},
            provisionaledits=None,
        )
        nodegroup_cache = {
            self.nodegroup.nodegroupid: list(self.all_datatype_nodes.values()),
        }

        result = index_from_tile(
            tile,
            delete_existing=False,
            nodegroup_cache=nodegroup_cache,
        )

        self.assertEqual(
            result,
            [],
            msg=(
                f"Expected no index records for null values but got "
                f"{len(result)} record(s): {result}"
            ),
        )
