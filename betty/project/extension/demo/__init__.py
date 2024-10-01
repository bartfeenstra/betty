"""
Provide demonstration site functionality.
"""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty import serve
from betty.ancestry.presence import Presence
from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Marriage, Birth, Death
from betty.ancestry.link import Link
from betty.ancestry.name import Name
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.place import Place
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.source import Source
from betty.date import Date, DateRange
from betty.project.extension.cotton_candy import CottonCandy
from betty.project.extension.cotton_candy.config import CottonCandyConfiguration
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.extension.maps import Maps
from betty.project.extension.trees import Trees
from betty.project.extension.wikipedia import Wikipedia
from betty.locale.localizable import static
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import ShorthandPluginBase
from betty.project import Project
from betty.project import load, generate
from betty.project.config import (
    LocaleConfiguration,
    ExtensionConfiguration,
    EntityReference,
)
from betty.project.extension import Extension
from betty.project.load import LoadAncestryEvent
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError

if TYPE_CHECKING:
    from betty.plugin import PluginIdentifier
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.app import App
    from collections.abc import AsyncIterator
    from betty.model import Entity


async def _load_ancestry(event: LoadAncestryEvent) -> None:
    def _load(*entities: Entity):
        event.project.ancestry.add(*entities)

    netherlands = Place(
        id="betty-demo-netherlands",
        names=[
            Name(
                {
                    "en": "Netherlands",
                    "nl": "Nederland",
                    "uk": "Нідерланди",
                    "fr": "Pays-Bas",
                }
            ),
        ],
        links=[Link("https://en.wikipedia.org/wiki/Netherlands")],
    )
    _load(netherlands)

    north_holland = Place(
        id="betty-demo-north-holland",
        names=[
            Name(
                {
                    "en": "North Holland",
                    "nl": "Noord-Holland",
                    "uk": "Північна Голландія",
                    "fr": "Hollande-Septentrionale",
                }
            ),
        ],
        links=[
            Link("https://en.wikipedia.org/wiki/North_Holland"),
            Link("https://www.noord-holland.nl/Home"),
        ],
    )
    _load(Enclosure(enclosee=north_holland, encloser=netherlands))
    _load(north_holland)

    amsterdam_note = Note(
        """
Did you know that while Amsterdam is the country's official capital, The Hague is the Netherlands' administrative center and seat of government?
    """
    )

    amsterdam = Place(
        id="betty-demo-amsterdam",
        names=[
            Name({"nl": "Amsterdam", "uk": "Амстерда́м"}),
        ],
        links=[
            Link("https://nl.wikipedia.org/wiki/Amsterdam"),
            Link("https://www.amsterdam.nl/"),
        ],
        notes=[amsterdam_note],
    )
    _load(Enclosure(enclosee=amsterdam, encloser=north_holland))
    _load(amsterdam)

    ilpendam = Place(
        id="betty-demo-ilpendam",
        names=[
            Name(
                {
                    "nl": "Ilpendam",
                    "uk": "Илпендам",
                }
            ),
        ],
        links=[Link("https://nl.wikipedia.org/wiki/Ilpendam")],
    )
    _load(Enclosure(enclosee=ilpendam, encloser=north_holland))
    _load(ilpendam)

    personal_accounts = Source(
        id="betty-demo-personal-accounts",
        name="Personal accounts",
    )
    _load(personal_accounts)

    cite_first_person_account = Citation(
        id="betty-demo-first-person-account",
        source=personal_accounts,
    )
    _load(cite_first_person_account)

    noord_hollands_archief = Source(
        id="betty-demo-noord-hollands-archief",
        name="Noord-Hollands Archief",
        links=[Link("https://noord-hollandsarchief.nl/")],
    )
    _load(noord_hollands_archief)

    bevolkingsregister_amsterdam = Source(
        id="betty-demo-bevolkingsregister-amsterdam",
        name="Bevolkingsregister Amsterdam",
        author="Gemeente Amsterdam",
        publisher="Gemeente Amsterdam",
        contained_by=noord_hollands_archief,
    )
    _load(bevolkingsregister_amsterdam)

    david_marinus_lankester = Person(id="betty-demo-david-marinus-lankester")
    _load(
        PersonName(
            person=david_marinus_lankester,
            individual="David Marinus",
            affiliation="Lankester",
        ),
        david_marinus_lankester,
    )

    geertruida_van_ling = Person(id="betty-demo-geertruida-van-ling")
    _load(
        PersonName(
            person=geertruida_van_ling,
            individual="Geertruida",
            affiliation="Van Ling",
        ),
        geertruida_van_ling,
    )

    marriage_of_dirk_jacobus_lankester_and_jannigje_palsen = Event(
        id="betty-demo-marriage-of-dirk-jacobus-lankester-and-jannigje-palsen",
        event_type=Marriage(),
        date=Date(1922, 7, 4),
        place=ilpendam,
    )
    _load(marriage_of_dirk_jacobus_lankester_and_jannigje_palsen)

    birth_of_dirk_jacobus_lankester = Event(
        id="betty-demo-birth-of-dirk-jacobus-lankester",
        event_type=Birth(),
        date=Date(1897, 8, 25),
        place=amsterdam,
    )
    _load(birth_of_dirk_jacobus_lankester)

    death_of_dirk_jacobus_lankester = Event(
        id="betty-demo-death-of-dirk-jacobus-lankester",
        event_type=Death(),
        date=Date(1986, 8, 18),
        place=amsterdam,
    )
    _load(death_of_dirk_jacobus_lankester)

    dirk_jacobus_lankester = Person(
        id="betty-demo-dirk-jacobus-lankester",
        parents=(david_marinus_lankester, geertruida_van_ling),
    )
    _load(
        PersonName(
            person=dirk_jacobus_lankester,
            individual="Dirk Jacobus",
            affiliation="Lankester",
        ),
        Presence(dirk_jacobus_lankester, Subject(), birth_of_dirk_jacobus_lankester),
        Presence(dirk_jacobus_lankester, Subject(), death_of_dirk_jacobus_lankester),
        Presence(
            dirk_jacobus_lankester,
            Subject(),
            marriage_of_dirk_jacobus_lankester_and_jannigje_palsen,
        ),
    )
    _load(dirk_jacobus_lankester)

    birth_of_marinus_david_lankester = Event(
        id="betty-demo-birth-of-marinus-david",
        event_type=Birth(),
        date=DateRange(
            Date(1874, 1, 15),
            Date(1874, 3, 21),
            start_is_boundary=True,
            end_is_boundary=True,
        ),
        place=amsterdam,
    )
    _load(birth_of_marinus_david_lankester)

    death_of_marinus_david_lankester = Event(
        id="betty-demo-death-of-marinus-david",
        event_type=Death(),
        date=Date(1971),
        place=amsterdam,
    )
    _load(death_of_marinus_david_lankester)

    marinus_david_lankester = Person(
        id="betty-demo-marinus-david-lankester",
        parents=(david_marinus_lankester, geertruida_van_ling),
    )
    _load(
        PersonName(
            person=marinus_david_lankester,
            individual="Marinus David",
            affiliation="Lankester",
        ),
        Presence(marinus_david_lankester, Subject(), birth_of_marinus_david_lankester),
        Presence(marinus_david_lankester, Subject(), death_of_marinus_david_lankester),
    )
    _load(marinus_david_lankester)

    birth_of_jacoba_gesina_lankester = Event(
        id="betty-demo-birth-of-jacoba-gesina",
        event_type=Birth(),
        date=Date(1900, 3, 14),
        place=amsterdam,
    )
    _load(birth_of_jacoba_gesina_lankester)

    jacoba_gesina_lankester = Person(
        id="betty-demo-jacoba-gesina-lankester",
        parents=(david_marinus_lankester, geertruida_van_ling),
    )
    _load(
        PersonName(
            person=jacoba_gesina_lankester,
            individual="Jacoba Gesina",
            affiliation="Lankester",
        ),
        Presence(jacoba_gesina_lankester, Subject(), birth_of_jacoba_gesina_lankester),
    )
    _load(jacoba_gesina_lankester)

    jannigje_palsen = Person(id="betty-demo-jannigje-palsen")
    _load(
        PersonName(
            person=jannigje_palsen,
            individual="Jannigje",
            affiliation="Palsen",
        ),
        Presence(
            jannigje_palsen,
            Subject(),
            marriage_of_dirk_jacobus_lankester_and_jannigje_palsen,
        ),
        jannigje_palsen,
    )

    marriage_of_johan_de_boer_and_liberta_lankester = Event(
        id="betty-demo-marriage-of-johan-de-boer-and-liberta-lankester",
        event_type=Marriage(),
        date=Date(1953, 6, 19),
        place=amsterdam,
    )
    _load(marriage_of_johan_de_boer_and_liberta_lankester)

    cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam = Citation(
        id="betty-demo-birth-of-liberta-lankester-from-bevolkingsregister-amsterdam",
        source=bevolkingsregister_amsterdam,
        location="Amsterdam",
    )
    _load(cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam)

    birth_of_liberta_lankester = Event(
        id="betty-demo-birth-of-liberta-lankester",
        event_type=Birth(),
        date=Date(1929, 12, 22),
        place=amsterdam,
        citations=[cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam],
    )
    _load(birth_of_liberta_lankester)

    death_of_liberta_lankester = Event(
        id="betty-demo-death-of-liberta-lankester",
        event_type=Death(),
        date=Date(2015, 1, 17),
        place=amsterdam,
        citations=[cite_first_person_account],
    )
    _load(death_of_liberta_lankester)

    liberta_lankester_note = Note(
        """
Did you know that Liberta "Betty" Lankester is Betty's namesake?
    """
    )

    liberta_lankester = Person(
        id="betty-demo-liberta-lankester",
        parents=(dirk_jacobus_lankester, jannigje_palsen),
        notes=[liberta_lankester_note],
    )
    _load(
        PersonName(
            person=liberta_lankester,
            individual="Liberta",
            affiliation="Lankester",
        ),
        PersonName(
            person=liberta_lankester,
            individual="Betty",
        ),
        Presence(liberta_lankester, Subject(), birth_of_liberta_lankester),
        Presence(liberta_lankester, Subject(), death_of_liberta_lankester),
        Presence(
            liberta_lankester,
            Subject(),
            marriage_of_johan_de_boer_and_liberta_lankester,
        ),
    )
    _load(liberta_lankester)

    birth_of_johan_de_boer = Event(
        id="betty-demo-birth-of-johan-de-boer",
        event_type=Birth(),
        date=Date(1930, 6, 20),
        place=amsterdam,
    )
    _load(birth_of_johan_de_boer)

    death_of_johan_de_boer = Event(
        id="betty-demo-death-of-johan-de-boer",
        event_type=Death(),
        date=Date(1999, 3, 10),
        place=amsterdam,
        citations=[cite_first_person_account],
    )
    _load(death_of_johan_de_boer)

    johan_de_boer = Person(id="betty-demo-johan-de-boer")
    _load(
        PersonName(
            person=johan_de_boer,
            individual="Johan",
            affiliation="De Boer",
        ),
        PersonName(
            person=johan_de_boer,
            individual="Hans",
        ),
        Presence(johan_de_boer, Subject(), birth_of_johan_de_boer),
        Presence(johan_de_boer, Subject(), death_of_johan_de_boer),
        Presence(
            johan_de_boer,
            Subject(),
            marriage_of_johan_de_boer_and_liberta_lankester,
        ),
        johan_de_boer,
    )

    parent_of_bart_feenstra_child_of_liberta_lankester = Person(
        id="betty-demo-parent-of-bart-feenstra-child-of-liberta-lankester",
        parents=(johan_de_boer, liberta_lankester),
    )
    _load(
        PersonName(
            person=parent_of_bart_feenstra_child_of_liberta_lankester,
            individual="Bart's parent",
        )
    )
    _load(parent_of_bart_feenstra_child_of_liberta_lankester)

    bart_feenstra = Person(
        id="betty-demo-bart-feenstra",
        parents=(parent_of_bart_feenstra_child_of_liberta_lankester,),
    )
    _load(
        PersonName(
            person=bart_feenstra,
            individual="Bart",
            affiliation="Feenstra",
        )
    )
    _load(bart_feenstra)


@final
class Demo(ShorthandPluginBase, Extension):
    """
    Provide demonstration site functionality.
    """

    _plugin_id = "demo"
    _plugin_label = static("Demo")

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {
            CottonCandy,
            HttpApiDoc,
            Maps,
            Trees,
            Wikipedia,
        }

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(LoadAncestryEvent, _load_ancestry)


@final
class DemoServer(Server):
    """
    Serve the Betty demonstration site.
    """

    def __init__(
        self,
        app: App,
    ):
        super().__init__(localizer=DEFAULT_LOCALIZER)
        self._app = app
        self._server: Server | None = None
        self._exit_stack = AsyncExitStack()

    @override
    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    @override
    async def start(self) -> None:
        try:
            project = await self._exit_stack.enter_async_context(
                demo_project(self._app)
            )
            self._localizer = await self._app.localizer
            await load.load(project)
            self._server = await serve.BuiltinProjectServer.new_for_project(project)
            await self._exit_stack.enter_async_context(self._server)
            project.configuration.url = self._server.public_url
            await generate.generate(project)
        except BaseException:
            await self.stop()
            raise

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()


@asynccontextmanager
async def demo_project(app: App) -> AsyncIterator[Project]:
    """
    Create a new demonstration project.
    """
    async with Project.new_temporary(app) as project:
        project.configuration.name = Demo.plugin_id()
        project.configuration.title = {
            "en-US": "A Betty demonstration",
            "nl-NL": "Een demonstratie van Betty",
        }
        project.configuration.author = {
            "en-US": "Bart Feenstra and contributors",
            "nl-NL": "Bart Feenstra en bijdragers",
        }
        project.configuration.extensions.append(ExtensionConfiguration(Demo))
        project.configuration.extensions.append(
            ExtensionConfiguration(
                CottonCandy,
                extension_configuration=CottonCandyConfiguration(
                    featured_entities=[
                        EntityReference(Place, "betty-demo-amsterdam"),
                        EntityReference(Person, "betty-demo-liberta-lankester"),
                        EntityReference(Place, "betty-demo-netherlands"),
                    ],
                ),
            )
        )
        # Include all of the translations Betty ships with.
        project.configuration.locales.replace(
            LocaleConfiguration(
                "en-US",
                alias="en",
            ),
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            ),
            LocaleConfiguration(
                "fr-FR",
                alias="fr",
            ),
            LocaleConfiguration(
                "uk",
                alias="uk",
            ),
            LocaleConfiguration(
                "de-DE",
                alias="de",
            ),
        )
        async with project:
            yield project
