"""
Provide the demonstration project.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, TYPE_CHECKING

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
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.source import Source
from betty.date import Date, DateRange
from betty.project import Project
from betty.project.config import (
    ExtensionConfiguration,
    EntityReference,
    LocaleConfiguration,
)
from betty.project.extension.cotton_candy import CottonCandy
from betty.project.extension.cotton_candy.config import CottonCandyConfiguration
from betty.typing import internal

if TYPE_CHECKING:
    from betty.ancestry import Ancestry
    from betty.app import App


@asynccontextmanager
async def create_project(app: App) -> AsyncIterator[Project]:
    """
    Create a new demonstration project.
    """
    from betty.project.extension.demo import Demo

    async with Project.new_temporary(app) as project:
        project.configuration.name = Demo.plugin_id()
        project.configuration.license = "spdx-gpl-3--0-or-later"
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


@internal
async def load_ancestry(ancestry: Ancestry) -> None:
    """
    Load the demo ancestry.
    """
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
    ancestry.add(netherlands)

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
    ancestry.add(Enclosure(enclosee=north_holland, encloser=netherlands))
    ancestry.add(north_holland)

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
    ancestry.add(Enclosure(enclosee=amsterdam, encloser=north_holland))
    ancestry.add(amsterdam)

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
    ancestry.add(Enclosure(enclosee=ilpendam, encloser=north_holland))
    ancestry.add(ilpendam)

    personal_accounts = Source(
        id="betty-demo-personal-accounts",
        name="Personal accounts",
    )
    ancestry.add(personal_accounts)

    cite_first_person_account = Citation(
        id="betty-demo-first-person-account",
        source=personal_accounts,
    )
    ancestry.add(cite_first_person_account)

    noord_hollands_archief = Source(
        id="betty-demo-noord-hollands-archief",
        name="Noord-Hollands Archief",
        links=[Link("https://noord-hollandsarchief.nl/")],
    )
    ancestry.add(noord_hollands_archief)

    bevolkingsregister_amsterdam = Source(
        id="betty-demo-bevolkingsregister-amsterdam",
        name="Bevolkingsregister Amsterdam",
        author="Gemeente Amsterdam",
        publisher="Gemeente Amsterdam",
        contained_by=noord_hollands_archief,
    )
    ancestry.add(bevolkingsregister_amsterdam)

    david_marinus_lankester = Person(id="betty-demo-david-marinus-lankester")
    ancestry.add(
        PersonName(
            person=david_marinus_lankester,
            individual="David Marinus",
            affiliation="Lankester",
        ),
        david_marinus_lankester,
    )

    geertruida_van_ling = Person(id="betty-demo-geertruida-van-ling")
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
        parents=(david_marinus_lankester, geertruida_van_ling),
    )
    ancestry.add(
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
        parents=(david_marinus_lankester, geertruida_van_ling),
    )
    ancestry.add(
        PersonName(
            person=marinus_david_lankester,
            individual="Marinus David",
            affiliation="Lankester",
        ),
        Presence(marinus_david_lankester, Subject(), birth_of_marinus_david_lankester),
        Presence(marinus_david_lankester, Subject(), death_of_marinus_david_lankester),
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
        parents=(david_marinus_lankester, geertruida_van_ling),
    )
    ancestry.add(
        PersonName(
            person=jacoba_gesina_lankester,
            individual="Jacoba Gesina",
            affiliation="Lankester",
        ),
        Presence(jacoba_gesina_lankester, Subject(), birth_of_jacoba_gesina_lankester),
    )
    ancestry.add(jacoba_gesina_lankester)

    jannigje_palsen = Person(id="betty-demo-jannigje-palsen")
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
        location="Amsterdam",
    )
    ancestry.add(cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam)

    birth_of_liberta_lankester = Event(
        id="betty-demo-birth-of-liberta-lankester",
        event_type=Birth(),
        date=Date(1929, 12, 22),
        place=amsterdam,
        citations=[cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam],
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
        """
Did you know that Liberta "Betty" Lankester is Betty's namesake?
    """
    )

    liberta_lankester = Person(
        id="betty-demo-liberta-lankester",
        parents=(dirk_jacobus_lankester, jannigje_palsen),
        notes=[liberta_lankester_note],
    )
    ancestry.add(
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

    johan_de_boer = Person(id="betty-demo-johan-de-boer")
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
        parents=(johan_de_boer, liberta_lankester),
    )
    ancestry.add(
        PersonName(
            person=parent_of_bart_feenstra_child_of_liberta_lankester,
            individual="Bart's parent",
        )
    )
    ancestry.add(parent_of_bart_feenstra_child_of_liberta_lankester)

    bart_feenstra = Person(
        id="betty-demo-bart-feenstra",
        parents=(parent_of_bart_feenstra_child_of_liberta_lankester,),
    )
    ancestry.add(
        PersonName(
            person=bart_feenstra,
            individual="Bart",
            affiliation="Feenstra",
        )
    )
    ancestry.add(bart_feenstra)
