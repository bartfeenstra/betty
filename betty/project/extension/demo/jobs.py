"""
Jobs.
"""

from __future__ import annotations

from random import choice
from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth, Death, Marriage
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.gender.genders import Female, Male
from betty.ancestry.link import Link
from betty.ancestry.name import Name
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.place import Place
from betty.ancestry.place_type.place_types import (
    Country,
    Municipality,
    Province,
    Village,
)
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.source import Source
from betty.date import Date, DateRange
from betty.dirs import DATA_DIRECTORY_PATH
from betty.job import Job
from betty.license import LicenseDefinition
from betty.license.licenses import spdx_license_id_to_license_id
from betty.locale.localizable import Plain, _
from betty.media_type.media_types import SVG
from betty.project import Project, ProjectContext
from betty.project.extension.demo.copyright_notice import Streetmix

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.job.scheduler import Scheduler
    from betty.machine_name import MachineName


class LoadAncestry(Job[ProjectContext]):
    """
    Load the demonstration data into an ancestry.
    """

    def __init__(self):
        super().__init__("demo:load-ancestry")

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        ancestry = project.ancestry

        (
            streetmix_files_per_gender,
            fallback_streetmix_files,
        ) = await self._load_streetmix_images(project)

        def _streetmix_image(person: Person) -> None:
            if person.file_references:
                return

            try:
                streetmix_files = streetmix_files_per_gender[person.gender.plugin.id]
            except KeyError:
                streetmix_files = fallback_streetmix_files
            streetmix_file = choice(streetmix_files)
            ancestry.add(FileReference(person, streetmix_file))

        netherlands = Place(
            id="betty-demo-netherlands",
            names=[
                Name(_("Netherlands")),
            ],
            links=[Link("https://en.wikipedia.org/wiki/Netherlands")],
            place_type=Country(),
        )
        ancestry.add(netherlands)

        north_holland = Place(
            id="betty-demo-north-holland",
            names=[
                Name(_("North Holland")),
            ],
            links=[
                Link("https://en.wikipedia.org/wiki/North_Holland"),
                Link("https://www.noord-holland.nl/"),
            ],
            place_type=Province(),
        )
        ancestry.add(Enclosure(enclosee=north_holland, encloser=netherlands))
        ancestry.add(north_holland)

        amsterdam_note = Note(
            _(
                "Did you know that while Amsterdam is the country's official capital, The Hague is the Netherlands' administrative center and seat of government?"
            )
        )

        amsterdam = Place(
            id="betty-demo-amsterdam",
            names=[
                Name(_("Amsterdam")),
            ],
            links=[
                Link("https://nl.wikipedia.org/wiki/Amsterdam"),
                Link("https://www.amsterdam.nl/"),
            ],
            notes=[amsterdam_note],
            place_type=Municipality(),
        )
        ancestry.add(Enclosure(enclosee=amsterdam, encloser=north_holland))
        ancestry.add(amsterdam)

        ilpendam = Place(
            id="betty-demo-ilpendam",
            names=[
                Name(_("Ilpendam")),
            ],
            links=[Link("https://nl.wikipedia.org/wiki/Ilpendam")],
            place_type=Village(),
        )
        ancestry.add(Enclosure(enclosee=ilpendam, encloser=north_holland))
        ancestry.add(ilpendam)

        personal_accounts = Source(
            id="betty-demo-personal-accounts",
            name=_("Personal accounts"),
        )
        ancestry.add(personal_accounts)

        cite_first_person_account = Citation(
            id="betty-demo-first-person-account",
            source=personal_accounts,
            location=Plain("Bart Feenstra"),
        )
        ancestry.add(cite_first_person_account)

        noord_hollands_archief = Source(
            id="betty-demo-noord-hollands-archief",
            name=Plain("Noord-Hollands Archief"),
            links=[Link("https://noord-hollandsarchief.nl/")],
        )
        ancestry.add(noord_hollands_archief)

        bevolkingsregister_amsterdam = Source(
            id="betty-demo-bevolkingsregister-amsterdam",
            name=Plain("Bevolkingsregister Amsterdam"),
            author=_("Gemeente Amsterdam"),
            publisher=_("Gemeente Amsterdam"),
            contained_by=noord_hollands_archief,
        )
        ancestry.add(bevolkingsregister_amsterdam)

        david_marinus_lankester = Person(
            id="betty-demo-david-marinus-lankester", gender=Male()
        )
        _streetmix_image(david_marinus_lankester)
        ancestry.add(
            PersonName(
                person=david_marinus_lankester,
                individual="David Marinus",
                affiliation="Lankester",
            ),
            david_marinus_lankester,
        )

        geertruida_van_ling = Person(
            id="betty-demo-geertruida-van-ling", gender=Female()
        )
        _streetmix_image(geertruida_van_ling)
        ancestry.add(
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
        ancestry.add(marriage_of_dirk_jacobus_lankester_and_jannigje_palsen)

        birth_of_dirk_jacobus_lankester = Event(
            id="betty-demo-birth-of-dirk-jacobus-lankester",
            event_type=Birth(),
            date=Date(1897, 8, 25),
            place=amsterdam,
        )
        ancestry.add(birth_of_dirk_jacobus_lankester)

        death_of_dirk_jacobus_lankester = Event(
            id="betty-demo-death-of-dirk-jacobus-lankester",
            event_type=Death(),
            date=Date(1986, 8, 18),
            place=amsterdam,
        )
        ancestry.add(death_of_dirk_jacobus_lankester)

        dirk_jacobus_lankester = Person(
            id="betty-demo-dirk-jacobus-lankester",
            gender=Male(),
            parents=[david_marinus_lankester, geertruida_van_ling],
        )
        _streetmix_image(dirk_jacobus_lankester)
        ancestry.add(
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
        ancestry.add(dirk_jacobus_lankester)

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
        ancestry.add(birth_of_marinus_david_lankester)

        death_of_marinus_david_lankester = Event(
            id="betty-demo-death-of-marinus-david",
            event_type=Death(),
            date=Date(1971),
            place=amsterdam,
        )
        ancestry.add(death_of_marinus_david_lankester)

        marinus_david_lankester = Person(
            id="betty-demo-marinus-david-lankester",
            gender=Male(),
            parents=[david_marinus_lankester, geertruida_van_ling],
        )
        _streetmix_image(marinus_david_lankester)
        ancestry.add(
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
        ancestry.add(marinus_david_lankester)

        birth_of_jacoba_gesina_lankester = Event(
            id="betty-demo-birth-of-jacoba-gesina",
            event_type=Birth(),
            date=Date(1900, 3, 14),
            place=amsterdam,
        )
        ancestry.add(birth_of_jacoba_gesina_lankester)

        jacoba_gesina_lankester = Person(
            id="betty-demo-jacoba-gesina-lankester",
            gender=Female(),
            parents=[david_marinus_lankester, geertruida_van_ling],
        )
        _streetmix_image(jacoba_gesina_lankester)
        ancestry.add(
            PersonName(
                person=jacoba_gesina_lankester,
                individual="Jacoba Gesina",
                affiliation="Lankester",
            ),
            Presence(
                jacoba_gesina_lankester, Subject(), birth_of_jacoba_gesina_lankester
            ),
        )
        ancestry.add(jacoba_gesina_lankester)

        jannigje_palsen = Person(id="betty-demo-jannigje-palsen", gender=Female())
        _streetmix_image(jannigje_palsen)
        ancestry.add(
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
        ancestry.add(marriage_of_johan_de_boer_and_liberta_lankester)

        cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam = Citation(
            id="betty-demo-birth-of-liberta-lankester-from-bevolkingsregister-amsterdam",
            source=bevolkingsregister_amsterdam,
            location=_("Amsterdam"),
            date=DateRange(None, Date(2000, 1, 1), end_is_boundary=True),
        )
        ancestry.add(cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam)

        birth_of_liberta_lankester = Event(
            id="betty-demo-birth-of-liberta-lankester",
            event_type=Birth(),
            date=Date(1929, 12, 22),
            place=amsterdam,
            citations=[
                cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam
            ],
        )
        ancestry.add(birth_of_liberta_lankester)

        death_of_liberta_lankester = Event(
            id="betty-demo-death-of-liberta-lankester",
            event_type=Death(),
            date=Date(2015, 1, 17),
            place=amsterdam,
            citations=[cite_first_person_account],
        )
        ancestry.add(death_of_liberta_lankester)

        liberta_lankester_note = Note(
            _('Did you know that Liberta "Betty" Lankester is Betty\'s namesake?')
        )

        liberta_lankester = Person(
            id="betty-demo-liberta-lankester",
            gender=Female(),
            parents=[dirk_jacobus_lankester, jannigje_palsen],
            notes=[liberta_lankester_note],
        )
        _streetmix_image(liberta_lankester)
        ancestry.add(
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
        ancestry.add(liberta_lankester)

        birth_of_johan_de_boer = Event(
            id="betty-demo-birth-of-johan-de-boer",
            event_type=Birth(),
            date=Date(1930, 6, 20),
            place=amsterdam,
        )
        ancestry.add(birth_of_johan_de_boer)

        death_of_johan_de_boer = Event(
            id="betty-demo-death-of-johan-de-boer",
            event_type=Death(),
            date=Date(1999, 3, 10),
            place=amsterdam,
            citations=[cite_first_person_account],
        )
        ancestry.add(death_of_johan_de_boer)

        johan_de_boer = Person(id="betty-demo-johan-de-boer", gender=Male())
        _streetmix_image(johan_de_boer)
        ancestry.add(
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
        ancestry.add(
            PersonName(
                person=parent_of_bart_feenstra_child_of_liberta_lankester,
                individual="Bart's parent",
            )
        )
        ancestry.add(parent_of_bart_feenstra_child_of_liberta_lankester)

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
        ancestry.add(birth_of_johan_de_boer)

        bart_feenstra = Person(
            id="betty-demo-bart-feenstra",
            gender=Male(),
            parents=[parent_of_bart_feenstra_child_of_liberta_lankester],
        )
        Presence(bart_feenstra, Subject(), birth_of_bart_feenstra)
        _streetmix_image(bart_feenstra)
        ancestry.add(
            PersonName(
                person=bart_feenstra,
                individual="Bart",
                affiliation="Feenstra",
            )
        )
        ancestry.add(bart_feenstra)

    async def _load_streetmix_images(
        self,
        project: Project,
    ) -> tuple[Mapping[MachineName, Sequence[File]], Sequence[File]]:
        licenses = await project.plugins(LicenseDefinition)
        license = await project.new_target(  # noqa A001
            licenses[spdx_license_id_to_license_id("AGPL-3.0-or-later")].cls
        )
        copyright_notice = await project.new_target(Streetmix)
        streetmix_image_directory_path = DATA_DIRECTORY_PATH / "images" / "streetmix"
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
                streetmix_image_directory_path / file_name,
                id=f"streetmix-{file_name}",
                media_type=SVG,
                copyright_notice=copyright_notice,
                license=license,
            )
            appearance.append(file)
            project.ancestry.add(file)

        return {
            Female.plugin.id: feminine + androgynous,
            Male.plugin.id: masculine + androgynous,
        }, androgynous
