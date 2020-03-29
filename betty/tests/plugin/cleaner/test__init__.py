from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry, Person, Event, Place, Presence, LocalizedName, IdentifiableEvent, File, \
    PersonName, IdentifiableSource, IdentifiableCitation
from betty.config import Configuration
from betty.functools import sync
from betty.parse import parse
from betty.plugin.cleaner import Cleaner, clean
from betty.site import Site


class CleanerTest(TestCase):
    @sync
    async def test_post_parse(self) -> None:
        event = IdentifiableEvent('E0', Event.Type.BIRTH)
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Cleaner] = {}
            async with Site(configuration) as site:
                site.ancestry.events[event.id] = event
                await parse(site)
                self.assertEquals({}, site.ancestry.events)


class CleanTest(TestCase):
    def test_clean(self) -> None:
        ancestry = Ancestry()

        onymous_event = IdentifiableEvent('E0', Event.Type.BIRTH)
        Presence(Person('P0'), Presence.Role.SUBJECT, onymous_event)
        ancestry.events[onymous_event.id] = onymous_event

        anonymous_event = IdentifiableEvent('E1', Event.Type.BIRTH)
        ancestry.events[anonymous_event.id] = anonymous_event

        onymous_place = Place('P0', [LocalizedName('Amsterdam')])
        onymous_place.events.append(onymous_event)
        ancestry.places[onymous_place.id] = onymous_place

        anonymous_place = Place('P1', [LocalizedName('Almelo')])
        ancestry.places[anonymous_place.id] = anonymous_place

        onmyous_place_because_encloses_onmyous_places = Place(
            'P3', [LocalizedName('Netherlands')])
        onmyous_place_because_encloses_onmyous_places.encloses.append(
            onymous_place)
        onmyous_place_because_encloses_onmyous_places.encloses.append(
            anonymous_place)
        ancestry.places[
            onmyous_place_because_encloses_onmyous_places.id] = onmyous_place_because_encloses_onmyous_places

        clean(ancestry)

        self.assertDictEqual({
            onymous_event.id: onymous_event,
        }, ancestry.events)
        self.assertDictEqual({
            onymous_place.id: onymous_place,
            onmyous_place_because_encloses_onmyous_places.id: onmyous_place_because_encloses_onmyous_places,
        }, ancestry.places)

        self.assertNotIn(
            anonymous_place, onmyous_place_because_encloses_onmyous_places.encloses)

    def test_clean_should_not_clean_person_if_public(self):
        ancestry = Ancestry()

        person = Person('P0')
        person.private = False
        ancestry.people[person.id] = person

        clean(ancestry)

        self.assertEqual(person, ancestry.people[person.id])

    def test_clean_should_clean_person_with_private_children(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        person.private = True
        ancestry.people[person.id] = person
        child = Person('P1')
        child.private = True
        ancestry.people[child.id] = child
        grandchild = Person('P2')
        grandchild.private = True
        ancestry.people[grandchild.id] = grandchild
        great_grandchild = Person('P3')
        great_grandchild.private = True
        ancestry.people[great_grandchild.id] = great_grandchild

        clean(ancestry)

        self.assertNotIn(person.id, ancestry.people)

    def test_clean_should_not_clean_person_with_public_children(self):
        ancestry = Ancestry()

        person = Person('P0')
        person.private = False
        ancestry.people[person.id] = person
        child = Person('P1')
        child.private = True
        ancestry.people[child.id] = child
        grandchild = Person('P2')
        grandchild.private = True
        ancestry.people[grandchild.id] = grandchild
        great_grandchild = Person('P3')
        great_grandchild.private = False
        ancestry.people[great_grandchild.id] = great_grandchild

        clean(ancestry)

        self.assertEqual(person, ancestry.people[person.id])

    def test_clean_should_clean_event(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S1', 'The Source')
        ancestry.sources[source.id] = source

        citation = IdentifiableCitation('C1', source)
        ancestry.citations[citation.id] = citation

        file = File('F1', __file__)
        ancestry.files[file.id] = file

        place = Place('P0', [LocalizedName('The Place')])
        ancestry.places[place.id] = place

        event = IdentifiableEvent('E0', Event.Type.BIRTH)
        event.citations.append(citation)
        event.files.append(file)
        event.place = place
        ancestry.events[event.id] = event

        clean(ancestry)

        self.assertNotIn(event.id, ancestry.events)
        self.assertIsNone(event.place)
        self.assertNotIn(event, place.events)
        self.assertNotIn(place.id, ancestry.places)
        self.assertNotIn(event, citation.facts)
        self.assertNotIn(citation.id, ancestry.citations)
        self.assertNotIn(event, file.resources)
        self.assertNotIn(file.id, ancestry.files)

    def test_clean_should_not_clean_event_with_presences_with_people(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S1', 'The Source')
        ancestry.sources[source.id] = source

        citation = IdentifiableCitation('C1', source)
        ancestry.citations[citation.id] = citation

        file = File('F1', __file__)
        ancestry.files[file.id] = file

        place = Place('P0', [LocalizedName('The Place')])
        ancestry.places[place.id] = place

        person = Person('P0')

        event = IdentifiableEvent('E0', Event.Type.BIRTH)
        event.citations.append(citation)
        event.files.append(file)
        event.place = place
        ancestry.events[event.id] = event

        Presence(person, Presence.Role.SUBJECT, event)

        clean(ancestry)

        self.assertEqual(event, ancestry.events[event.id])
        self.assertIn(event, place.events)
        self.assertEqual(place, ancestry.places[place.id])
        self.assertIn(event, citation.facts)
        self.assertEqual(citation, ancestry.citations[citation.id])
        self.assertIn(event, file.resources)
        self.assertEqual(file, ancestry.files[file.id])

    def test_clean_should_clean_file(self) -> None:
        ancestry = Ancestry()

        file = File('F0', __file__)
        ancestry.files[file.id] = file

        clean(ancestry)

        self.assertNotIn(file.id, ancestry.files)

    def test_clean_should_not_clean_file_with_resources(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        ancestry.people[person.id] = person

        file = File('F0', __file__)
        file.resources.append(person)
        ancestry.files[file.id] = file

        clean(ancestry)

        self.assertEqual(file, ancestry.files[file.id])
        self.assertIn(person, file.resources)
        self.assertEqual(person, ancestry.people[person.id])

    def test_clean_should_clean_source(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S0', 'The source')
        ancestry.sources[source.id] = source

        clean(ancestry)

        self.assertNotIn(source.id, ancestry.sources)

    def test_clean_should_not_clean_source_with_citations(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S0', 'The Source')
        ancestry.sources[source.id] = source

        citation = IdentifiableCitation('C0', source)
        citation.facts.append(PersonName('Jane'))
        ancestry.citations[citation.id] = citation

        clean(ancestry)

        self.assertEqual(source, ancestry.sources[source.id])
        self.assertEqual(source, citation.source)
        self.assertEqual(citation, ancestry.citations[citation.id])

    def test_clean_should_not_clean_source_with_contained_by(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S0', 'The Source')
        ancestry.sources[source.id] = source

        contained_by = IdentifiableSource('S1', 'The Source')
        contained_by.contains.append(source)
        ancestry.sources[contained_by.id] = contained_by

        clean(ancestry)

        self.assertEqual(source, ancestry.sources[source.id])
        self.assertIn(source, contained_by.contains)
        self.assertEqual(contained_by, ancestry.sources[contained_by.id])

    def test_clean_should_not_clean_source_with_contains(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S0', 'The Source')
        ancestry.sources[source.id] = source

        contains = IdentifiableSource('S1', 'The Source')
        contains.contained_by = source
        ancestry.sources[contains.id] = contains

        clean(ancestry)

        self.assertEqual(source, ancestry.sources[source.id])
        self.assertEqual(source, contains.contained_by)
        self.assertEqual(contains, ancestry.sources[contains.id])

    def test_clean_should_not_clean_source_with_files(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S0', 'The Source')
        ancestry.sources[source.id] = source

        file = File('F0', __file__)
        file.resources.append(source)
        ancestry.files[file.id] = file

        clean(ancestry)

        self.assertEqual(source, ancestry.sources[source.id])
        self.assertIn(source, file.sources)
        self.assertEqual(file, ancestry.files[file.id])

    def test_clean_should_clean_citation(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S0', 'The source')
        ancestry.sources[source.id] = source

        citation = IdentifiableCitation('C0', source)
        ancestry.citations[citation.id] = citation

        clean(ancestry)

        self.assertNotIn(citation.id, ancestry.citations)
        self.assertNotIn(citation, source.citations)

    def test_clean_should_not_clean_citation_with_facts(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S0', 'The Source')
        ancestry.sources[source.id] = source

        citation = IdentifiableCitation('C0', source)
        citation.facts.append(PersonName('Jane'))
        ancestry.citations[citation.id] = citation

        fact = Person('P0')
        fact.citations.append(citation)
        ancestry.people[fact.id] = fact

        clean(ancestry)

        self.assertEqual(citation, ancestry.citations[citation.id])
        self.assertIn(citation, fact.citations)
        self.assertEqual(fact, ancestry.people[fact.id])

    def test_clean_should_not_clean_citation_with_files(self) -> None:
        ancestry = Ancestry()

        source = IdentifiableSource('S0', 'The Source')
        ancestry.sources[source.id] = source

        citation = IdentifiableCitation('C0', source)
        ancestry.citations[citation.id] = citation

        file = File('F0', __file__)
        file.resources.append(citation)
        ancestry.files[file.id] = file

        clean(ancestry)

        self.assertEqual(citation, ancestry.citations[citation.id])
        self.assertIn(citation, file.citations)
        self.assertEqual(file, ancestry.files[file.id])
        self.assertIn(citation, source.citations)
        self.assertEqual(source, ancestry.sources[source.id])
