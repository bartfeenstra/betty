from __future__ import annotations

from contextlib import AsyncExitStack

from geopy import Point

from betty import load, generate
from betty.app import App
from betty.app.extension import Extension
from betty.load import Loader
from betty.locale import Date, DateRange, Str
from betty.model import Entity
from betty.model.ancestry import Place, PlaceName, Person, Presence, Subject, PersonName, Link, Source, Citation, Event, \
    Enclosure
from betty.model.event_type import Marriage, Birth, Death
from betty.project import LocaleConfiguration, ExtensionConfiguration, EntityReference
from betty.serve import Server, AppServer, NoPublicUrlBecauseServerNotStartedError


class _Demo(Extension, Loader):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        from betty.extension import CottonCandy, HttpApiDoc, Maps, Trees, Wikipedia

        return {CottonCandy, HttpApiDoc, Maps, Trees, Wikipedia}

    def _load(self, *entities: Entity) -> None:
        self._app.project.ancestry.add(*entities)

    async def load(self) -> None:
        from betty.extension import CottonCandy

        netherlands = Place(
            id='betty-demo-netherlands',
            names=[
                PlaceName(name='Netherlands'),
                PlaceName(
                    name='Nederland',
                    locale='nl',
                ),
                PlaceName(
                    name='Нідерланди',
                    locale='uk',
                ),
                PlaceName(
                    name='Pays-Bas',
                    locale='fr',
                ),
            ],
            links={Link('https://en.wikipedia.org/wiki/Netherlands')},
        )
        self._load(netherlands)

        north_holland = Place(
            id='betty-demo-north-holland',
            names=[
                PlaceName(name='North Holland'),
                PlaceName(
                    name='Noord-Holland',
                    locale='nl',
                ),
                PlaceName(
                    name='Північна Голландія',
                    locale='uk',
                ),
                PlaceName(
                    name='Hollande-Septentrionale',
                    locale='fr',
                ),
            ],
            links={Link('https://en.wikipedia.org/wiki/North_Holland')},
        )
        self._load(Enclosure(encloses=north_holland, enclosed_by=netherlands))
        self._load(north_holland)

        amsterdam = Place(
            id='betty-demo-amsterdam',
            names=[
                PlaceName(name='Amsterdam'),
                PlaceName(
                    name='Амстерда́м',
                    locale='uk',
                ),
            ],
            coordinates=Point(52.366667, 4.9),
            links={Link('https://nl.wikipedia.org/wiki/Amsterdam')},
        )
        self._load(Enclosure(encloses=amsterdam, enclosed_by=north_holland))
        self._load(amsterdam)

        ilpendam = Place(
            id='betty-demo-ilpendam',
            names=[
                PlaceName(name='Ilpendam'),
                PlaceName(
                    name='Илпендам',
                    locale='uk',
                ),
            ],
            coordinates=Point(52.465556, 4.951111),
            links={Link('https://nl.wikipedia.org/wiki/Ilpendam')},
        )
        self._load(Enclosure(encloses=ilpendam, enclosed_by=north_holland))
        self._load(ilpendam)

        personal_accounts = Source(
            id='betty-demo-personal-accounts',
            name='Personal accounts',
        )
        self._load(personal_accounts)

        cite_first_person_account = Citation(
            id='betty-demo-first-person-account',
            source=personal_accounts,
        )
        self._load(cite_first_person_account)

        bevolkingsregister_amsterdam = Source(
            id='betty-demo-bevolkingsregister-amsterdam',
            name='Bevolkingsregister Amsterdam',
            author='Gemeente Amsterdam',
            publisher='Gemeente Amsterdam',
        )
        self._load(bevolkingsregister_amsterdam)

        david_marinus_lankester = Person(id='betty-demo-david-marinus-lankester')
        self._load(
            PersonName(
                person=david_marinus_lankester,
                individual='David Marinus',
                affiliation='Lankester',
            ),
            david_marinus_lankester,
        )

        geertruida_van_ling = Person(id='betty-demo-geertruida-van-ling')
        self._load(
            PersonName(
                person=geertruida_van_ling,
                individual='Geertruida',
                affiliation='Van Ling',
            ),
            geertruida_van_ling,
        )

        marriage_of_dirk_jacobus_lankester_and_jannigje_palsen = Event(
            id='betty-demo-marriage-of-dirk-jacobus-lankester-and-jannigje-palsen',
            event_type=Marriage,
            date=Date(1922, 7, 4),
            place=ilpendam,
        )
        self._load(marriage_of_dirk_jacobus_lankester_and_jannigje_palsen)

        birth_of_dirk_jacobus_lankester = Event(
            id='betty-demo-birth-of-dirk-jacobus-lankester',
            event_type=Birth,
            date=Date(1897, 8, 25),
            place=amsterdam,
        )
        self._load(birth_of_dirk_jacobus_lankester)

        death_of_dirk_jacobus_lankester = Event(
            id='betty-demo-death-of-dirk-jacobus-lankester',
            event_type=Death,
            date=Date(1986, 8, 18),
            place=amsterdam,
        )
        self._load(death_of_dirk_jacobus_lankester)

        dirk_jacobus_lankester = Person(
            id='betty-demo-dirk-jacobus-lankester',
            parents=(david_marinus_lankester, geertruida_van_ling)
        )
        self._load(
            PersonName(
                person=dirk_jacobus_lankester,
                individual='Dirk Jacobus',
                affiliation='Lankester',
            ),
            Presence(dirk_jacobus_lankester, Subject(), birth_of_dirk_jacobus_lankester),
            Presence(dirk_jacobus_lankester, Subject(), death_of_dirk_jacobus_lankester),
            Presence(dirk_jacobus_lankester, Subject(), marriage_of_dirk_jacobus_lankester_and_jannigje_palsen),
        )
        self._load(dirk_jacobus_lankester)

        birth_of_marinus_david_lankester = Event(
            id='betty-demo-birth-of-marinus-david',
            event_type=Birth,
            date=DateRange(Date(1874, 1, 15), Date(1874, 3, 21), start_is_boundary=True, end_is_boundary=True),
            place=amsterdam,
        )
        self._load(birth_of_marinus_david_lankester)

        death_of_marinus_david_lankester = Event(
            id='betty-demo-death-of-marinus-david',
            event_type=Death,
            date=Date(1971),
            place=amsterdam,
        )
        self._load(death_of_marinus_david_lankester)

        marinus_david_lankester = Person(
            id='betty-demo-marinus-david-lankester',
            parents=(david_marinus_lankester, geertruida_van_ling),
        )
        self._load(
            PersonName(
                person=marinus_david_lankester,
                individual='Marinus David',
                affiliation='Lankester',
            ),
            Presence(marinus_david_lankester, Subject(), birth_of_marinus_david_lankester),
            Presence(marinus_david_lankester, Subject(), death_of_marinus_david_lankester),
        )
        self._load(marinus_david_lankester)

        birth_of_jacoba_gesina_lankester = Event(
            id='betty-demo-birth-of-jacoba-gesina',
            event_type=Birth,
            date=Date(1900, 3, 14),
            place=amsterdam,
        )
        self._load(birth_of_jacoba_gesina_lankester)

        jacoba_gesina_lankester = Person(
            id='betty-demo-jacoba-gesina-lankester',
            parents=(david_marinus_lankester, geertruida_van_ling),
        )
        self._load(
            PersonName(
                person=jacoba_gesina_lankester,
                individual='Jacoba Gesina',
                affiliation='Lankester',
            ),
            Presence(jacoba_gesina_lankester, Subject(), birth_of_jacoba_gesina_lankester),
        )
        self._load(jacoba_gesina_lankester)

        jannigje_palsen = Person(id='betty-demo-jannigje-palsen')
        self._load(
            PersonName(
                person=jannigje_palsen,
                individual='Jannigje',
                affiliation='Palsen',
            ),
            Presence(jannigje_palsen, Subject(), marriage_of_dirk_jacobus_lankester_and_jannigje_palsen),
            jannigje_palsen,
        )

        marriage_of_johan_de_boer_and_liberta_lankester = Event(
            id='betty-demo-marriage-of-johan-de-boer-and-liberta-lankester',
            event_type=Marriage,
            date=Date(1953, 6, 19),
            place=amsterdam,
        )
        self._load(marriage_of_johan_de_boer_and_liberta_lankester)

        cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam = Citation(
            id='betty-demo-birth-of-liberta-lankester-from-bevolkingsregister-amsterdam',
            source=bevolkingsregister_amsterdam,
            location=Str.plain('Amsterdam'),
        )
        self._load(cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam)

        birth_of_liberta_lankester = Event(
            id='betty-demo-birth-of-liberta-lankester',
            event_type=Birth,
            date=Date(1929, 12, 22),
            place=amsterdam,
            citations=[cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam],
        )
        self._load(birth_of_liberta_lankester)

        death_of_liberta_lankester = Event(
            id='betty-demo-death-of-liberta-lankester',
            event_type=Death,
            date=Date(2015, 1, 17),
            place=amsterdam,
            citations=[cite_first_person_account],
        )
        self._load(death_of_liberta_lankester)

        liberta_lankester = Person(
            id='betty-demo-liberta-lankester',
            parents=(dirk_jacobus_lankester, jannigje_palsen),
        )
        self._load(
            PersonName(
                person=liberta_lankester,
                individual='Liberta',
                affiliation='Lankester',
            ),
            PersonName(
                person=liberta_lankester,
                individual='Betty',
            ),
            Presence(liberta_lankester, Subject(), birth_of_liberta_lankester),
            Presence(liberta_lankester, Subject(), death_of_liberta_lankester),
            Presence(liberta_lankester, Subject(), marriage_of_johan_de_boer_and_liberta_lankester),
        )
        self._load(liberta_lankester)

        birth_of_johan_de_boer = Event(
            id='betty-demo-birth-of-johan-de-boer',
            event_type=Birth,
            date=Date(1930, 6, 20),
            place=amsterdam,
        )
        self._load(birth_of_johan_de_boer)

        death_of_johan_de_boer = Event(
            id='betty-demo-death-of-johan-de-boer',
            event_type=Death,
            date=Date(1999, 3, 10),
            place=amsterdam,
            citations=[cite_first_person_account],
        )
        self._load(death_of_johan_de_boer)

        johan_de_boer = Person(id='betty-demo-johan-de-boer')
        self._load(
            PersonName(
                person=johan_de_boer,
                individual='Johan',
                affiliation='De Boer',
            ),
            PersonName(
                person=johan_de_boer,
                individual='Hans',
            ),
            Presence(johan_de_boer, Subject(), birth_of_johan_de_boer),
            Presence(johan_de_boer, Subject(), death_of_johan_de_boer),
            Presence(johan_de_boer, Subject(), marriage_of_johan_de_boer_and_liberta_lankester),
            johan_de_boer,
        )

        parent_of_bart_feenstra_child_of_liberta_lankester = Person(
            id='betty-demo-parent-of-bart-feenstra-child-of-liberta-lankester',
            parents=(johan_de_boer, liberta_lankester),
        )
        self._load(PersonName(
            person=parent_of_bart_feenstra_child_of_liberta_lankester,
            individual='Bart\'s parent',
        ))
        self._load(parent_of_bart_feenstra_child_of_liberta_lankester)

        bart_feenstra = Person(
            id='betty-demo-bart-feenstra',
            parents=(parent_of_bart_feenstra_child_of_liberta_lankester,),
        )
        self._load(PersonName(
            person=bart_feenstra,
            individual='Bart',
            affiliation='Feenstra',
        ))
        self._load(bart_feenstra)

        theme = self.app.extensions[CottonCandy]
        theme.configuration.featured_entities.append(EntityReference(Person, 'betty-demo-liberta-lankester'))
        theme.configuration.featured_entities.append(EntityReference(Place, 'betty-demo-amsterdam'))


class DemoServer(Server):
    def __init__(self):
        self._app = App()
        super().__init__(self._app.localizer)
        self._app.project.configuration.extensions.append(ExtensionConfiguration(_Demo))
        # Include all of the translations Betty ships with.
        self._app.project.configuration.locales.replace(
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('fr-FR', 'fr'),
            LocaleConfiguration('uk', 'uk'),
        )
        self._server: Server | None = None
        self._exit_stack = AsyncExitStack()

    @classmethod
    def label(cls) -> Str:
        return Str._('Demo')

    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    async def start(self) -> None:
        try:
            await super().start()
            await self._exit_stack.enter_async_context(self._app)
            await load.load(self._app)
            self._server = AppServer.get(self._app)
            await self._exit_stack.enter_async_context(self._server)
            self._app.project.configuration.base_url = self._server.public_url
            await generate.generate(self._app)
        finally:
            await self.stop()

    async def stop(self) -> None:
        await self._exit_stack.aclose()
        await super().stop()
