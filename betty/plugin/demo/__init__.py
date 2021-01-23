from typing import Any, Set, Type

from geopy import Point

from betty.ancestry import Place, PlaceName, Person, Ancestry, Presence, Subject, Birth, IdentifiableEvent, \
    PersonName, IdentifiableSource, IdentifiableCitation, Link, Death, Marriage
from betty.site import Site
from betty.plugin import Plugin, NO_CONFIGURATION
from betty.plugin.wikipedia import Wikipedia
from betty.parse import Parser
from betty.locale import Date, DateRange


class Demo(Plugin, Parser):
    def __init__(self, ancestry: Ancestry):
        self._ancestry = ancestry

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(site.ancestry)

    @classmethod
    def depends_on(cls) -> Set[Type[Plugin]]:
        return {Wikipedia}

    async def parse(self) -> None:
        amsterdam = Place('betty-demo-amsterdam', [PlaceName('Amsterdam')])
        amsterdam.coordinates = Point(52.366667, 4.9)
        amsterdam.links.add(Link('https://nl.wikipedia.org/wiki/Amsterdam'))
        self._ancestry.places[amsterdam.id] = amsterdam

        ilpendam = Place('betty-demo-ilpendam', [PlaceName('Ilpendam')])
        ilpendam.coordinates = Point(52.465556, 4.951111)
        ilpendam.links.add(Link('https://nl.wikipedia.org/wiki/Ilpendam'))
        self._ancestry.places[ilpendam.id] = ilpendam

        personal_accounts = IdentifiableSource('betty-demo-personal-accounts', 'Personal accounts')
        self._ancestry.sources[personal_accounts.id] = personal_accounts

        cite_first_person_account = IdentifiableCitation('betty-demo-first-person-account', personal_accounts)
        self._ancestry.citations[cite_first_person_account.id] = cite_first_person_account

        bevolkingsregister_amsterdam = IdentifiableSource('betty-demo-bevolkingsregister-amsterdam', 'Bevolkingsregister Amsterdam')
        bevolkingsregister_amsterdam.author = 'Gemeente Amsterdam'
        bevolkingsregister_amsterdam.publisher = 'Gemeente Amsterdam'
        self._ancestry.sources[bevolkingsregister_amsterdam.id] = bevolkingsregister_amsterdam

        david_marinus_lankester = Person('betty-demo-david-marinus-lankester')
        david_marinus_lankester.names.append(PersonName('David Marinus', 'Lankester'))
        self._ancestry.people[david_marinus_lankester.id] = david_marinus_lankester

        geertruida_van_ling = Person('betty-demo-geertruida-van-ling')
        geertruida_van_ling.names.append(PersonName('Geertruida', 'Van Ling'))
        self._ancestry.people[geertruida_van_ling.id] = geertruida_van_ling

        marriage_of_dirk_jacobus_lankester_and_jannigje_palsen = IdentifiableEvent('betty-demo-marriage-of-dirk-jacobus-lankester-and-jannigje-palsen', Marriage(), Date(1922, 7, 4))
        marriage_of_dirk_jacobus_lankester_and_jannigje_palsen.place = ilpendam
        self._ancestry.events[marriage_of_dirk_jacobus_lankester_and_jannigje_palsen.id] = marriage_of_dirk_jacobus_lankester_and_jannigje_palsen

        birth_of_dirk_jacobus_lankester = IdentifiableEvent('betty-demo-birth-of-dirk-jacobus-lankester', Birth(), Date(1897, 8, 25))
        birth_of_dirk_jacobus_lankester.place = amsterdam
        self._ancestry.events[birth_of_dirk_jacobus_lankester.id] = birth_of_dirk_jacobus_lankester

        death_of_dirk_jacobus_lankester = IdentifiableEvent('betty-demo-death-of-dirk-jacobus-lankester', Death(), Date(1986, 8, 18))
        death_of_dirk_jacobus_lankester.place = amsterdam
        self._ancestry.events[death_of_dirk_jacobus_lankester.id] = death_of_dirk_jacobus_lankester

        dirk_jacobus_lankester = Person('betty-demo-dirk-jacobus-lankester')
        dirk_jacobus_lankester.names.append(PersonName('Dirk Jacobus', 'Lankester'))
        Presence(dirk_jacobus_lankester, Subject(), birth_of_dirk_jacobus_lankester)
        Presence(dirk_jacobus_lankester, Subject(), death_of_dirk_jacobus_lankester)
        Presence(dirk_jacobus_lankester, Subject(), marriage_of_dirk_jacobus_lankester_and_jannigje_palsen)
        dirk_jacobus_lankester.parents.append(david_marinus_lankester, geertruida_van_ling)
        self._ancestry.people[dirk_jacobus_lankester.id] = dirk_jacobus_lankester

        birth_of_marinus_david_lankester = IdentifiableEvent('betty-demo-birth-of-marinus-david', Birth(), DateRange(Date(1874, 1, 15), Date(1874, 3, 21), start_is_boundary=True, end_is_boundary=True))
        birth_of_marinus_david_lankester.place = amsterdam
        self._ancestry.events[birth_of_marinus_david_lankester.id] = birth_of_marinus_david_lankester

        death_of_marinus_david_lankester = IdentifiableEvent('betty-demo-death-of-marinus-david', Death(), Date(1971))
        death_of_marinus_david_lankester.place = amsterdam
        self._ancestry.events[death_of_marinus_david_lankester.id] = death_of_marinus_david_lankester

        marinus_david_lankester = Person('betty-demo-marinus-david-lankester')
        marinus_david_lankester.names.append(PersonName('Marinus David', 'Lankester'))
        Presence(marinus_david_lankester, Subject(), birth_of_marinus_david_lankester)
        Presence(marinus_david_lankester, Subject(), death_of_marinus_david_lankester)
        marinus_david_lankester.parents.append(david_marinus_lankester, geertruida_van_ling)
        self._ancestry.people[marinus_david_lankester.id] = marinus_david_lankester

        birth_of_jacoba_gesina_lankester = IdentifiableEvent('betty-demo-birth-of-jacoba-gesina', Birth(), Date(1900, 3, 14))
        birth_of_jacoba_gesina_lankester.place = amsterdam
        self._ancestry.events[birth_of_jacoba_gesina_lankester.id] = birth_of_jacoba_gesina_lankester

        jacoba_gesina_lankester = Person('betty-demo-jacoba-gesina-lankester')
        jacoba_gesina_lankester.names.append(PersonName('Jacoba Gesina', 'Lankester'))
        Presence(jacoba_gesina_lankester, Subject(), birth_of_jacoba_gesina_lankester)
        jacoba_gesina_lankester.parents.append(david_marinus_lankester, geertruida_van_ling)
        self._ancestry.people[jacoba_gesina_lankester.id] = jacoba_gesina_lankester

        jannigje_palsen = Person('betty-demo-jannigje-palsen')
        jannigje_palsen.names.append(PersonName('Jannigje', 'Palsen'))
        Presence(jannigje_palsen, Subject(), marriage_of_dirk_jacobus_lankester_and_jannigje_palsen)
        self._ancestry.people[jannigje_palsen.id] = jannigje_palsen

        marriage_of_johan_de_boer_and_liberta_lankester = IdentifiableEvent('betty-demo-marriage-of-johan-de-boer-and-liberta-lankester', Marriage(), Date(1953, 6, 19))
        marriage_of_johan_de_boer_and_liberta_lankester.place = amsterdam
        self._ancestry.events[marriage_of_johan_de_boer_and_liberta_lankester.id] = marriage_of_johan_de_boer_and_liberta_lankester

        cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam = IdentifiableCitation('betty-demo-birth-of-liberta-lankester-from-bevolkingsregister-amsterdam', bevolkingsregister_amsterdam)
        cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam.location = 'Amsterdam'
        self._ancestry.citations[cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam.id] = cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam

        birth_of_liberta_lankester = IdentifiableEvent('betty-demo-birth-of-liberta-lankester', Birth(), Date(1929, 12, 22))
        birth_of_liberta_lankester.place = amsterdam
        birth_of_liberta_lankester.citations.append(cite_birth_of_liberta_lankester_from_bevolkingsregister_amsterdam)
        self._ancestry.events[birth_of_liberta_lankester.id] = birth_of_liberta_lankester

        death_of_liberta_lankester = IdentifiableEvent('betty-demo-death-of-liberta-lankester', Death(), Date(2015, 1, 17))
        death_of_liberta_lankester.place = amsterdam
        death_of_liberta_lankester.citations.append(cite_first_person_account)
        self._ancestry.events[death_of_liberta_lankester.id] = death_of_liberta_lankester

        liberta_lankester = Person('betty-demo-liberta-lankester')
        liberta_lankester.names.append(PersonName('Liberta', 'Lankester'))
        liberta_lankester.names.append(PersonName('Betty'))
        Presence(liberta_lankester, Subject(), birth_of_liberta_lankester)
        Presence(liberta_lankester, Subject(), death_of_liberta_lankester)
        Presence(liberta_lankester, Subject(), marriage_of_johan_de_boer_and_liberta_lankester)
        liberta_lankester.parents.append(dirk_jacobus_lankester, jannigje_palsen)
        self._ancestry.people[liberta_lankester.id] = liberta_lankester

        birth_of_johan_de_boer = IdentifiableEvent('betty-demo-birth-of-johan-de-boer', Birth(), Date(1930, 6, 20))
        birth_of_johan_de_boer.place = amsterdam
        self._ancestry.events[birth_of_johan_de_boer.id] = birth_of_johan_de_boer

        death_of_johan_de_boer = IdentifiableEvent('betty-demo-death-of-johan-de-boer', Death(), Date(1999, 3, 10))
        death_of_johan_de_boer.place = amsterdam
        death_of_johan_de_boer.citations.append(cite_first_person_account)
        self._ancestry.events[death_of_johan_de_boer.id] = death_of_johan_de_boer

        johan_de_boer = Person('betty-demo-johan-de-boer')
        johan_de_boer.names.append(PersonName('Johan', 'De Boer'))
        johan_de_boer.names.append(PersonName('Hans'))
        Presence(johan_de_boer, Subject(), birth_of_johan_de_boer)
        Presence(johan_de_boer, Subject(), death_of_johan_de_boer)
        Presence(johan_de_boer, Subject(), marriage_of_johan_de_boer_and_liberta_lankester)
        self._ancestry.people[johan_de_boer.id] = johan_de_boer

        parent_of_bart_feenstra_child_of_liberta_lankester = Person('betty-demo-parent-of-bart-feenstra-child-of-liberta-lankester')
        parent_of_bart_feenstra_child_of_liberta_lankester.names.append(PersonName('Bart\'s parent'))
        parent_of_bart_feenstra_child_of_liberta_lankester.parents.append(johan_de_boer, liberta_lankester)
        self._ancestry.people[parent_of_bart_feenstra_child_of_liberta_lankester.id] = parent_of_bart_feenstra_child_of_liberta_lankester

        bart_feenstra = Person('betty-demo-bart-feenstra')
        bart_feenstra.names.append(PersonName('Bart', 'Feenstra'))
        bart_feenstra.parents.append(parent_of_bart_feenstra_child_of_liberta_lankester)
        self._ancestry.people[bart_feenstra.id] = bart_feenstra
