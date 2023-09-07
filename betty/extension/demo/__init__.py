from __future__ import annotations

from geopy import Point

from betty import load, generate
from betty.app import App
from betty.app.extension import Extension
from betty.load import Loader
from betty.locale import Date, DateRange, Localizer
from betty.model import Entity
from betty.model.ancestry import Place, PlaceName, Person, Presence, Subject, PersonName, Link, Source, Citation, Event, \
    Enclosure
from betty.model.event_type import Marriage, Birth, Death
from betty.project import LocaleConfiguration, ExtensionConfiguration, EntityReference
from betty.serve import Server, ProjectServer, NoPublicUrlBecauseServerNotStartedError


class _Demo(Extension, Loader):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        from betty.extension import CottonCandy, HttpApiDoc, Maps, Trees, Wikipedia

        return {CottonCandy, HttpApiDoc, Maps, Trees, Wikipedia}

    def _load(self, *entities: Entity) -> None:
        self._app.project.ancestry.add(*entities)

    async def load(self) -> None:
        from betty.extension import CottonCandy

        netherlands = Place('betty-demo-netherlands', [
            PlaceName('Netherlands'),
            PlaceName('Nederland', locale='nl'),
            PlaceName('Нідерланди', locale='uk'),
            PlaceName('Pays-Bas', locale='fr'),
        ])
        netherlands.links.add(Link('https://en.wikipedia.org/wiki/Netherlands'))
        self._load(netherlands)

        north_holland = Place('betty-demo-north-holland', [
            PlaceName('North Holland'),
            PlaceName('Noord-Holland', locale='nl'),
            PlaceName('Північна Голландія', locale='uk'),
            PlaceName('Hollande-Septentrionale', locale='fr'),
        ])
        self._load(Enclosure(north_holland, netherlands))
        north_holland.links.add(Link('https://en.wikipedia.org/wiki/North_Holland'))
        self._load(north_holland)

        amsterdam = Place('betty-demo-amsterdam', [
            PlaceName('Amsterdam'),
            PlaceName('Амстерда́м', locale='uk'),
        ])
        self._load(Enclosure(amsterdam, north_holland))
        amsterdam.coordinates = Point(52.366667, 4.9)
        amsterdam.links.add(Link('https://nl.wikipedia.org/wiki/Amsterdam'))
        self._load(amsterdam)

        ilpendam = Place('betty-demo-ilpendam', [
            PlaceName('Ilpendam'),
            PlaceName('Илпендам', locale='uk'),
        ])
        self._load(Enclosure(ilpendam, north_holland))
        ilpendam.coordinates = Point(52.465556, 4.951111)
        ilpendam.links.add(Link('https://nl.wikipedia.org/wiki/Ilpendam'))
        self._load(ilpendam)

        personal_accounts = Source('betty-demo-personal-accounts', 'Personal accounts')
        self._load(personal_accounts)

        cite_first_person_account = Citation('betty-demo-first-person-account', personal_accounts)
        self._load(cite_first_person_account)

        bevolkingsregister_amsterdam = Source('betty-demo-bevolkingsregister-amsterdam', 'Bevolkingsregister Amsterdam')
        bevolkingsregister_amsterdam.author = 'Gemeente Amsterdam'
        bevolkingsregister_amsterdam.publisher = 'Gemeente Amsterdam'
        self._load(bevolkingsregister_amsterdam)

        david_marinus_lankester = Person('betty-demo-david-marinus-lankester')
        self._load(
            PersonName(None, david_marinus_lankester, 'David Marinus', 'Lankester'),
            david_marinus_lankester,
        )

        geertruida_van_ling = Person('betty-demo-geertruida-van-ling')
        self._load(
            PersonName(None, geertruida_van_ling, 'Geertruida', 'Van Ling'),
            geertruida_van_ling,
        )

        marriage_of_dirk_jacobus_lankester_and_jannigje_palsen = Event('betty-demo-marriage-of-dirk-jacobus-lankester-and-jannigje-palsen', Marriage, Date(1922, 7, 4))
        marriage_of_dirk_jacobus_lankester_and_jannigje_palsen.place = ilpendam
        self._load(marriage_of_dirk_jacobus_lankester_and_jannigje_palsen)

        birth_of_dirk_jacobus_lankester = Event('betty-demo-birth-of-dirk-jacobus-lankester', Birth, Date(1897, 8, 25))
        birth_of_dirk_jacobus_lankester.place = amsterdam
        self._load(birth_of_dirk_jacobus_lankester)

        death_of_dirk_jacobus_lankester = Event('betty-demo-death-of-dirk-jacobus-lankester', Death, Date(1986, 8, 18))
        death_of_dirk_jacobus_lankester.place = amsterdam
        self._load(death_of_dirk_jacobus_lankester)

        dirk_jacobus_lankester = Person('betty-demo-dirk-jacobus-lankester')
        self._load(
            PersonName(None, dirk_jacobus_lankester, 'Dirk Jacobus', 'Lankester'),
            Presence(None, dirk_jacobus_lankester, Subject(), birth_of_dirk_jacobus_lankester),
            Presence(None, dirk_jacobus_lankester, Subject(), death_of_dirk_jacobus_lankester),
            Presence(None, dirk_jacobus_lankester, Subject(), marriage_of_dirk_jacobus_lankester_and_jannigje_palsen),
        )
        dirk_jacobus_lankester.parents.add(david_marinus_lankester, geertruida_van_ling)
        self._load(dirk_jacobus_lankester)

        birth_of_marinus_david_lankester = Event('betty-demo-birth-of-marinus-david', Birth, DateRange(Date(1874, 1, 15), Date(1874, 3, 21), start_is_boundary=True, end_is_boundary=True))
        birth_of_marinus_david_lankester.place = amsterdam
        self._load(birth_of_marinus_david_lankester)

        death_of_marinus_david_lankester = Event('betty-demo-death-of-marinus-david', Death, Date(1971))
        death_of_marinus_david_lankester.place = amsterdam
        self._load(death_of_marinus_david_lankester)

        marinus_david_lankester = Person('betty-demo-marinus-david-lankester')
        self._load(
            PersonName(None, marinus_david_lankester, 'Marinus David', 'Lankester'),
            Presence(None, marinus_david_lankester, Subject(), birth_of_marinus_david_lankester),
            Presence(None, marinus_david_lankester, Subject(), death_of_marinus_david_lankester),
        )
        marinus_david_lankester.parents.add(david_marinus_lankester, geertruida_van_ling)
        self._load(marinus_david_lankester)

        birth_of_jacoba_gesina_lankester = Event('betty-demo-birth-of-jacoba-gesina', Birth, Date(1900, 3, 14))
        birth_of_jacoba_gesina_lankester.place = amsterdam
        self._load(birth_of_jacoba_gesina_lankester)

        jacoba_gesina_lankester = Person('betty-demo-jacoba-gesina-lankester')
        self._load(
            PersonName(None, jacoba_gesina_lankester, 'Jacoba Gesina', 'Lankester'),
            Presence(None, jacoba_gesina_lankester, Subject(), birth_of_jacoba_gesina_lankester),
        )
        jacoba_gesina_lankester.parents.add(david_marinus_lankester, geertruida_van_ling)
        self._load(jacoba_gesina_lankester)

        jannigje_palsen = Person('betty-demo-jannigje-palsen')
        self._load(
            PersonName(None, jannigje_palsen, 'Jannigje', 'Palsen'),
            Presence(None, jannigje_palsen, Subject(), marriage_of_dirk_jacobus_lankester_and_jannigje_palsen),
            jannigje_palsen,
        )

        marriage_of_johan_de_boer_and_liberta_lankester = Event('betty-demo-marriage-of-johan-de-boer-and-liberta-lankester', Marriage, Date(1953, 6, 19))
        marriage_of_johan_de_boer_and_liberta_lankester.place = amsterdam
        self._load(marriage_of_johan_de_boer_and_liberta_lankester)

        cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam = Citation('betty-demo-birth-of-liberta-lankester-from-bevolkingsregister-amsterdam', bevolkingsregister_amsterdam)
        cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam.location = 'Amsterdam'
        self._load(cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam)

        birth_of_liberta_lankester = Event('betty-demo-birth-of-liberta-lankester', Birth, Date(1929, 12, 22))
        birth_of_liberta_lankester.place = amsterdam
        birth_of_liberta_lankester.citations.add(cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam)
        self._load(birth_of_liberta_lankester)

        death_of_liberta_lankester = Event('betty-demo-death-of-liberta-lankester', Death, Date(2015, 1, 17))
        death_of_liberta_lankester.place = amsterdam
        death_of_liberta_lankester.citations.add(cite_first_person_account)
        self._load(death_of_liberta_lankester)

        liberta_lankester = Person('betty-demo-liberta-lankester')
        self._load(
            PersonName(None, liberta_lankester, 'Liberta', 'Lankester'),
            PersonName(None, liberta_lankester, 'Betty'),
            Presence(None, liberta_lankester, Subject(), birth_of_liberta_lankester),
            Presence(None, liberta_lankester, Subject(), death_of_liberta_lankester),
            Presence(None, liberta_lankester, Subject(), marriage_of_johan_de_boer_and_liberta_lankester),
        )
        liberta_lankester.parents.add(dirk_jacobus_lankester, jannigje_palsen)
        self._load(liberta_lankester)

        birth_of_johan_de_boer = Event('betty-demo-birth-of-johan-de-boer', Birth, Date(1930, 6, 20))
        birth_of_johan_de_boer.place = amsterdam
        self._load(birth_of_johan_de_boer)

        death_of_johan_de_boer = Event('betty-demo-death-of-johan-de-boer', Death, Date(1999, 3, 10))
        death_of_johan_de_boer.place = amsterdam
        death_of_johan_de_boer.citations.add(cite_first_person_account)
        self._load(death_of_johan_de_boer)

        johan_de_boer = Person('betty-demo-johan-de-boer')
        self._load(
            PersonName(None, johan_de_boer, 'Johan', 'De Boer'),
            PersonName(None, johan_de_boer, 'Hans'),
            Presence(None, johan_de_boer, Subject(), birth_of_johan_de_boer),
            Presence(None, johan_de_boer, Subject(), death_of_johan_de_boer),
            Presence(None, johan_de_boer, Subject(), marriage_of_johan_de_boer_and_liberta_lankester),
            johan_de_boer,
        )

        parent_of_bart_feenstra_child_of_liberta_lankester = Person('betty-demo-parent-of-bart-feenstra-child-of-liberta-lankester')
        self._load(PersonName(None, parent_of_bart_feenstra_child_of_liberta_lankester, 'Bart\'s parent'))
        parent_of_bart_feenstra_child_of_liberta_lankester.parents.add(johan_de_boer, liberta_lankester)
        self._load(parent_of_bart_feenstra_child_of_liberta_lankester)

        bart_feenstra = Person('betty-demo-bart-feenstra')
        self._load(PersonName(None, bart_feenstra, 'Bart', 'Feenstra'))
        bart_feenstra.parents.add(parent_of_bart_feenstra_child_of_liberta_lankester)
        self._load(bart_feenstra)

        theme = self.app.extensions[CottonCandy]
        theme.configuration.featured_entities.append(EntityReference(Person, 'betty-demo-liberta-lankester'))
        theme.configuration.featured_entities.append(EntityReference(Place, 'betty-demo-amsterdam'))


class DemoServer(Server):
    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._server: Server | None = None

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Demo')

    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    async def start(self) -> None:
        app = App(locale=self.localizer.locale)
        app.project.configuration.extensions.append(ExtensionConfiguration(_Demo))
        # Include all of the translations Betty ships with.
        app.project.configuration.locales.replace(
            LocaleConfiguration('en-US', 'en'),
            LocaleConfiguration('nl-NL', 'nl'),
            LocaleConfiguration('fr-FR', 'fr'),
            LocaleConfiguration('uk', 'uk'),
        )
        await load.load(app)
        self._server = ProjectServer.get(app)
        await self._server.start()
        app.project.configuration.base_url = self._server.public_url
        await generate.generate(app)

    async def stop(self) -> None:
        if self._server:
            await self._server.stop()
