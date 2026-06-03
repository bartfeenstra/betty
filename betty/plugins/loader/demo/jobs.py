"""
Jobs.
"""

from __future__ import annotations

from random import choice
from typing import TYPE_CHECKING, override

from betty.date import Date, DateRange
from betty.dirs import BUILTIN_ASSET_DIRECTORY
from betty.genders.man import Man
from betty.genders.woman import Woman
from betty.job import Job
from betty.locale.localizable.gettext import _
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.event import Event
from betty.plugins.entity.file import File
from betty.plugins.entity.file_reference import FileReference
from betty.plugins.entity.link import Link
from betty.plugins.entity.note import Note
from betty.plugins.entity.person import Person
from betty.plugins.entity.person_name import PersonName
from betty.plugins.entity.place import Place
from betty.plugins.entity.place_name import PlaceName
from betty.plugins.entity.presence import Presence
from betty.plugins.entity.source import Source
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.death import Death
from betty.plugins.event_type.marriage import Marriage
from betty.plugins.media_type.svg import SVG
from betty.plugins.place_type.country import Country
from betty.plugins.place_type.municipality import Municipality
from betty.plugins.place_type.province import Province
from betty.plugins.place_type.village import Village
from betty.plugins.role.subject import Subject

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.copyright_notice import CopyrightNotice
    from betty.entity.collection.pool import EntityPool
    from betty.factory import Factory
    from betty.job.scheduler import Scheduler
    from betty.license import License
    from betty.machine_name import MachineName


class LoadAncestry(Job):
    """
    Load the demonstration data into an ancestry.
    """

    def __init__(
        self,
        *,
        ancestry: EntityPool,
        factory: Factory,
        streetmix_copyright_notice: CopyrightNotice,
        streetmix_license: License,
    ):
        super().__init__("demo:load-ancestry")
        self._ancestry = ancestry
        self._factory = factory
        self._streetmix_copyright_notice = streetmix_copyright_notice
        self._streetmix_license = streetmix_license

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        (
            streetmix_files_per_gender,
            fallback_streetmix_files,
        ) = await self._load_streetmix_images()

        def _streetmix_image(person: Person) -> None:
            if person.file_references:
                return

            try:
                streetmix_files = streetmix_files_per_gender[person.gender.plugin().id]
            except KeyError:
                streetmix_files = fallback_streetmix_files
            streetmix_file = choice(streetmix_files)
            self._ancestry.add(FileReference(person, streetmix_file))

        netherlands = Place(
            id="betty-demo-netherlands",
            names=[
                PlaceName(_("Netherlands")),
            ],
            links=[Link("https://en.wikipedia.org/wiki/Netherlands")],
            place_type=Country(),
        )
        self._ancestry.add(netherlands)

        north_holland = Place(
            id="betty-demo-north-holland",
            names=[
                PlaceName(_("North Holland")),
            ],
            links=[
                Link("https://en.wikipedia.org/wiki/North_Holland"),
                Link("https://www.noord-holland.nl/"),
            ],
            place_type=Province(),
        )
        self._ancestry.add(Enclosure(enclosee=north_holland, encloser=netherlands))
        self._ancestry.add(north_holland)

        amsterdam_note = Note(
            _(
                "Did you know that while Amsterdam is the country's official capital, The Hague is the Netherlands' administrative center and seat of government?"
            )
        )

        amsterdam = Place(
            id="betty-demo-amsterdam",
            names=[
                PlaceName(_("Amsterdam")),
            ],
            links=[
                Link("https://nl.wikipedia.org/wiki/Amsterdam"),
                Link("https://www.amsterdam.nl/"),
            ],
            notes=[amsterdam_note],
            place_type=Municipality(),
        )
        self._ancestry.add(Enclosure(enclosee=amsterdam, encloser=north_holland))
        self._ancestry.add(amsterdam)

        ilpendam = Place(
            id="betty-demo-ilpendam",
            names=[
                PlaceName(_("Ilpendam")),
            ],
            links=[Link("https://nl.wikipedia.org/wiki/Ilpendam")],
            place_type=Village(),
        )
        self._ancestry.add(Enclosure(enclosee=ilpendam, encloser=north_holland))
        self._ancestry.add(ilpendam)

        personal_accounts = Source(
            id="betty-demo-personal-accounts",
            name=_("Personal accounts"),
        )
        self._ancestry.add(personal_accounts)

        cite_first_person_account = Citation(
            id="betty-demo-first-person-account",
            source=personal_accounts,
            location="Bart Feenstra",
        )
        self._ancestry.add(cite_first_person_account)

        noord_hollands_archief = Source(
            id="betty-demo-noord-hollands-archief",
            name="Noord-Hollands Archief",
            links=[Link("https://noord-hollandsarchief.nl/")],
        )
        self._ancestry.add(noord_hollands_archief)

        bevolkingsregister_amsterdam = Source(
            id="betty-demo-bevolkingsregister-amsterdam",
            name="Bevolkingsregister Amsterdam",
            author=_("Gemeente Amsterdam"),
            publisher=_("Gemeente Amsterdam"),
            contained_by=noord_hollands_archief,
        )
        self._ancestry.add(bevolkingsregister_amsterdam)

        david_marinus_lankester = Person(
            id="betty-demo-david-marinus-lankester", gender=Man()
        )
        _streetmix_image(david_marinus_lankester)
        self._ancestry.add(
            PersonName(
                person=david_marinus_lankester,
                individual="David Marinus",
                affiliation="Lankester",
            ),
            david_marinus_lankester,
        )

        geertruida_van_ling = Person(
            id="betty-demo-geertruida-van-ling", gender=Woman()
        )
        _streetmix_image(geertruida_van_ling)
        self._ancestry.add(
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
        self._ancestry.add(marriage_of_dirk_jacobus_lankester_and_jannigje_palsen)

        birth_of_dirk_jacobus_lankester = Event(
            id="betty-demo-birth-of-dirk-jacobus-lankester",
            event_type=Birth(),
            date=Date(1897, 8, 25),
            place=amsterdam,
        )
        self._ancestry.add(birth_of_dirk_jacobus_lankester)

        death_of_dirk_jacobus_lankester = Event(
            id="betty-demo-death-of-dirk-jacobus-lankester",
            event_type=Death(),
            date=Date(1986, 8, 18),
            place=amsterdam,
        )
        self._ancestry.add(death_of_dirk_jacobus_lankester)

        dirk_jacobus_lankester = Person(
            id="betty-demo-dirk-jacobus-lankester",
            gender=Man(),
            parents=[david_marinus_lankester, geertruida_van_ling],
        )
        _streetmix_image(dirk_jacobus_lankester)
        self._ancestry.add(
            PersonName(
                person=dirk_jacobus_lankester,
                individual="Dirk Jacobus",
                affiliation="Lankester",
            ),
            Presence(
                dirk_jacobus_lankester, Subject(), birth_of_dirk_jacobus_lankester
            ),
            Presence(
                dirk_jacobus_lankester, Subject(), death_of_dirk_jacobus_lankester
            ),
            Presence(
                dirk_jacobus_lankester,
                Subject(),
                marriage_of_dirk_jacobus_lankester_and_jannigje_palsen,
            ),
        )
        self._ancestry.add(dirk_jacobus_lankester)

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
        self._ancestry.add(birth_of_marinus_david_lankester)

        death_of_marinus_david_lankester = Event(
            id="betty-demo-death-of-marinus-david",
            event_type=Death(),
            date=Date(1971),
            place=amsterdam,
        )
        self._ancestry.add(death_of_marinus_david_lankester)

        marinus_david_lankester = Person(
            id="betty-demo-marinus-david-lankester",
            gender=Man(),
            parents=[david_marinus_lankester, geertruida_van_ling],
        )
        _streetmix_image(marinus_david_lankester)
        self._ancestry.add(
            PersonName(
                person=marinus_david_lankester,
                individual="Marinus David",
                affiliation="Lankester",
            ),
            Presence(
                marinus_david_lankester, Subject(), birth_of_marinus_david_lankester
            ),
            Presence(
                marinus_david_lankester, Subject(), death_of_marinus_david_lankester
            ),
        )
        self._ancestry.add(marinus_david_lankester)

        birth_of_jacoba_gesina_lankester = Event(
            id="betty-demo-birth-of-jacoba-gesina",
            event_type=Birth(),
            date=Date(1900, 3, 14),
            place=amsterdam,
        )
        self._ancestry.add(birth_of_jacoba_gesina_lankester)

        jacoba_gesina_lankester = Person(
            id="betty-demo-jacoba-gesina-lankester",
            gender=Woman(),
            parents=[david_marinus_lankester, geertruida_van_ling],
        )
        _streetmix_image(jacoba_gesina_lankester)
        self._ancestry.add(
            PersonName(
                person=jacoba_gesina_lankester,
                individual="Jacoba Gesina",
                affiliation="Lankester",
            ),
            Presence(
                jacoba_gesina_lankester, Subject(), birth_of_jacoba_gesina_lankester
            ),
        )
        self._ancestry.add(jacoba_gesina_lankester)

        jannigje_palsen = Person(id="betty-demo-jannigje-palsen", gender=Woman())
        _streetmix_image(jannigje_palsen)
        self._ancestry.add(
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
        self._ancestry.add(marriage_of_johan_de_boer_and_liberta_lankester)

        cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam = Citation(
            id="betty-demo-birth-of-liberta-lankester-from-bevolkingsregister-amsterdam",
            source=bevolkingsregister_amsterdam,
            location=_("Amsterdam"),
            date=DateRange(None, Date(2000, 1, 1), end_is_boundary=True),
        )
        self._ancestry.add(
            cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam
        )

        birth_of_liberta_lankester = Event(
            id="betty-demo-birth-of-liberta-lankester",
            event_type=Birth(),
            date=Date(1929, 12, 22),
            place=amsterdam,
            citations=[
                cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam
            ],
        )
        self._ancestry.add(birth_of_liberta_lankester)

        death_of_liberta_lankester = Event(
            id="betty-demo-death-of-liberta-lankester",
            event_type=Death(),
            date=Date(2015, 1, 17),
            place=amsterdam,
            citations=[cite_first_person_account],
        )
        self._ancestry.add(death_of_liberta_lankester)

        liberta_lankester_note = Note(
            _('Did you know that Liberta "Betty" Lankester is Betty\'s namesake?')
        )

        liberta_lankester = Person(
            id="betty-demo-liberta-lankester",
            gender=Woman(),
            parents=[dirk_jacobus_lankester, jannigje_palsen],
            notes=[liberta_lankester_note],
        )
        _streetmix_image(liberta_lankester)
        self._ancestry.add(
            PersonName(
                person=liberta_lankester,
                individual="Liberta",
                affiliation="Lankester",
            ),
            PersonName(
                person=liberta_lankester,
                individual="Betty",
                citations=[cite_first_person_account],
            ),
            Presence(liberta_lankester, Subject(), birth_of_liberta_lankester),
            Presence(liberta_lankester, Subject(), death_of_liberta_lankester),
            Presence(
                liberta_lankester,
                Subject(),
                marriage_of_johan_de_boer_and_liberta_lankester,
            ),
        )
        self._ancestry.add(liberta_lankester)

        birth_of_johan_de_boer = Event(
            id="betty-demo-birth-of-johan-de-boer",
            event_type=Birth(),
            date=Date(1930, 6, 20),
            place=amsterdam,
        )
        self._ancestry.add(birth_of_johan_de_boer)

        death_of_johan_de_boer = Event(
            id="betty-demo-death-of-johan-de-boer",
            event_type=Death(),
            date=Date(1999, 3, 10),
            place=amsterdam,
            citations=[cite_first_person_account],
        )
        self._ancestry.add(death_of_johan_de_boer)

        johan_de_boer = Person(id="betty-demo-johan-de-boer", gender=Man())
        _streetmix_image(johan_de_boer)
        self._ancestry.add(
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
            parents=[johan_de_boer, liberta_lankester],
        )
        _streetmix_image(parent_of_bart_feenstra_child_of_liberta_lankester)
        self._ancestry.add(
            PersonName(
                person=parent_of_bart_feenstra_child_of_liberta_lankester,
                individual="Bart's parent",
            )
        )
        self._ancestry.add(parent_of_bart_feenstra_child_of_liberta_lankester)

        birth_of_bart_feenstra = Event(
            id="betty-demo-birth-of-bart-feenstra",
            event_type=Birth(),
            date=DateRange(Date(1970, 1, 1), start_is_boundary=True),
            place=netherlands,
            citations=[cite_first_person_account],
            description=_(
                "The 'birth of the author', so to speak.",
            ),
        )
        self._ancestry.add(birth_of_johan_de_boer)

        bart_feenstra = Person(
            id="betty-demo-bart-feenstra",
            gender=Man(),
            parents=[parent_of_bart_feenstra_child_of_liberta_lankester],
        )
        Presence(bart_feenstra, Subject(), birth_of_bart_feenstra)
        _streetmix_image(bart_feenstra)
        self._ancestry.add(
            PersonName(
                person=bart_feenstra,
                individual="Bart",
                affiliation="Feenstra",
            )
        )
        self._ancestry.add(bart_feenstra)

    async def _load_streetmix_images(
        self,
    ) -> tuple[Mapping[MachineName, Sequence[File]], Sequence[File]]:
        streetmix_image_directory = BUILTIN_ASSET_DIRECTORY / "vendor" / "streetmix"
        masculine: Sequence[File] = []
        feminine: Sequence[File] = []
        androgynous: Sequence[File] = []
        file_names = [
            ("johnny-01.svg", masculine),
            ("johnny-02.svg", masculine),
            ("junebug-01.svg", feminine),
            ("junebug-02.svg", feminine),
            ("people-01.svg", feminine),
            ("people-02.svg", androgynous),
            ("people-06.svg", androgynous),
            ("people-07.svg", feminine),
            ("people-08.svg", feminine),
            ("people-09.svg", androgynous),
            ("people-11.svg", masculine),
            ("people-13.svg", feminine),
            ("people-14.svg", masculine),
            ("people-15.svg", masculine),
            ("people-16.svg", androgynous),
            ("people-17.svg", feminine),
            ("people-18.svg", feminine),
            ("people-19.svg", feminine),
            ("people-23.svg", feminine),
            ("people-24.svg", androgynous),
            ("people-31.svg", masculine),
        ]
        for file_name, appearance in file_names:
            file = File(
                streetmix_image_directory / file_name,
                id=f"streetmix-{file_name}",
                media_type=SVG,
                copyright_notice=self._streetmix_copyright_notice,
                license=self._streetmix_license,
            )
            appearance.append(file)
            self._ancestry.add(file)

        return {
            Woman.plugin().id: feminine + androgynous,
            Man.plugin().id: masculine + androgynous,
        }, androgynous
