from betty.app import App, AppExtensionConfiguration
from betty.asyncio import sync
from betty.cleaner import clean, Cleaner
from betty.load import load
from betty.model.ancestry import Ancestry, Person, Place, Presence, PlaceName, File, PersonName, Subject, \
    Enclosure, Source, Citation, Event
from betty.model.event_type import Birth
from betty.tests import TestCase


class CleanerTest(TestCase):
    @sync
    async def test_post_parse(self) -> None:
        event = Event('E0', Birth())
        async with App() as app:
            app.configuration.extensions.add(AppExtensionConfiguration(Cleaner))
            app.ancestry.entities.append(event)
            await load(app)
            self.assertEqual([], list(app.ancestry.entities[Event]))


class CleanTest(TestCase):
    def test_clean(self) -> None:
        ancestry = Ancestry()

        onymous_event = Event('E0', Birth())
        Presence(Person('P0'), Subject(), onymous_event)
        ancestry.entities.append(onymous_event)

        anonymous_event = Event('E1', Birth())
        ancestry.entities.append(anonymous_event)

        onymous_place = Place('P0', [PlaceName('Amsterdam')])
        onymous_place.events.append(onymous_event)
        ancestry.entities.append(onymous_place)

        anonymous_place = Place('P1', [PlaceName('Almelo')])
        ancestry.entities.append(anonymous_place)

        onmyous_place_because_encloses_onmyous_places = Place(
            'P3', [PlaceName('Netherlands')])
        Enclosure(onymous_place, onmyous_place_because_encloses_onmyous_places)
        Enclosure(anonymous_place, onmyous_place_because_encloses_onmyous_places)
        ancestry.entities.append(onmyous_place_because_encloses_onmyous_places)

        clean(ancestry)

        self.assertEqual([onymous_event], list(ancestry.entities[Event]))
        self.assertEqual([onymous_place, onmyous_place_because_encloses_onmyous_places], list(ancestry.entities[Place]))

        self.assertNotIn(
            anonymous_place, onmyous_place_because_encloses_onmyous_places.encloses)

    def test_clean_should_not_clean_person_if_public(self):
        ancestry = Ancestry()

        person = Person('P0')
        person.private = False
        ancestry.entities.append(person)

        clean(ancestry)

        self.assertEqual(person, ancestry.entities[Person][person.id])

    def test_clean_should_clean_person_with_private_children(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        person.private = True
        ancestry.entities.append(person)
        child = Person('P1')
        child.private = True
        ancestry.entities.append(child)
        grandchild = Person('P2')
        grandchild.private = True
        ancestry.entities.append(grandchild)
        great_grandchild = Person('P3')
        great_grandchild.private = True
        ancestry.entities.append(great_grandchild)

        clean(ancestry)

        self.assertNotIn(person.id, ancestry.entities[Person])

    def test_clean_should_not_clean_person_with_public_children(self):
        ancestry = Ancestry()

        person = Person('P0')
        person.private = False
        ancestry.entities.append(person)
        child = Person('P1')
        child.private = True
        ancestry.entities.append(child)
        grandchild = Person('P2')
        grandchild.private = True
        ancestry.entities.append(grandchild)
        great_grandchild = Person('P3')
        great_grandchild.private = False
        ancestry.entities.append(great_grandchild)

        clean(ancestry)

        self.assertEqual(person, ancestry.entities[Person][person.id])

    def test_clean_should_clean_event(self) -> None:
        ancestry = Ancestry()

        source = Source('S1', 'The Source')
        ancestry.entities.append(source)

        citation = Citation('C1', source)
        ancestry.entities.append(citation)

        file = File('F1', __file__)
        ancestry.entities.append(file)

        place = Place('P0', [PlaceName('The Place')])
        ancestry.entities.append(place)

        event = Event('E0', Birth())
        event.citations.append(citation)
        event.files.append(file)
        event.place = place
        ancestry.entities.append(event)

        clean(ancestry)

        self.assertNotIn(event.id, ancestry.entities[Event])
        self.assertIsNone(event.place)
        self.assertNotIn(event, place.events)
        self.assertNotIn(place.id, ancestry.entities[Place])
        self.assertNotIn(event, citation.facts)
        self.assertNotIn(citation.id, ancestry.entities[Citation])
        self.assertNotIn(event, file.entities)
        self.assertNotIn(file.id, ancestry.entities[File])

    def test_clean_should_not_clean_event_with_presences_with_people(self) -> None:
        ancestry = Ancestry()

        source = Source('S1', 'The Source')
        ancestry.entities.append(source)

        citation = Citation('C1', source)
        ancestry.entities.append(citation)

        file = File('F1', __file__)
        ancestry.entities.append(file)

        place = Place('P0', [PlaceName('The Place')])
        ancestry.entities.append(place)

        person = Person('P0')

        event = Event('E0', Birth())
        event.citations.append(citation)
        event.files.append(file)
        event.place = place
        ancestry.entities.append(event)

        Presence(person, Subject(), event)

        clean(ancestry)

        self.assertEqual(event, ancestry.entities[Event][event.id])
        self.assertIn(event, place.events)
        self.assertEqual(place, ancestry.entities[Place][place.id])
        self.assertIn(event, citation.facts)
        self.assertEqual(citation, ancestry.entities[Citation][citation.id])
        self.assertIn(event, file.entities)
        self.assertEqual(file, ancestry.entities[File][file.id])

    def test_clean_should_clean_file(self) -> None:
        ancestry = Ancestry()

        file = File('F0', __file__)
        ancestry.entities.append(file)

        clean(ancestry)

        self.assertNotIn(file.id, ancestry.entities[File])

    def test_clean_should_not_clean_file_with_entities(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        ancestry.entities.append(person)

        file = File('F0', __file__)
        file.entities.append(person)
        ancestry.entities.append(file)

        clean(ancestry)

        self.assertEqual(file, ancestry.entities[File][file.id])
        self.assertIn(person, file.entities)
        self.assertEqual(person, ancestry.entities[Person][person.id])

    def test_clean_should_not_clean_file_with_citations(self) -> None:
        ancestry = Ancestry()

        source = Source(None)

        citation = Citation('C1', source)
        ancestry.entities.append(citation)

        file = File('F0', __file__)
        file.citations.append(citation)
        ancestry.entities.append(file)

        clean(ancestry)

        self.assertEqual(file, ancestry.entities[File][file.id])
        self.assertIn(citation, file.citations)
        self.assertEqual(citation, ancestry.entities[Citation][citation.id])

    def test_clean_should_clean_source(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The source')
        ancestry.entities.append(source)

        clean(ancestry)

        self.assertNotIn(source.id, ancestry.entities[Source])

    def test_clean_should_not_clean_source_with_citations(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        citation = Citation('C0', source)
        citation.facts.append(PersonName(Person(None), 'Jane'))
        ancestry.entities.append(citation)

        clean(ancestry)

        self.assertEqual(source, ancestry.entities[Source][source.id])
        self.assertEqual(source, citation.source)
        self.assertEqual(citation, ancestry.entities[Citation][citation.id])

    def test_clean_should_not_clean_source_with_contained_by(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        contained_by = Source('S1', 'The Source')
        contained_by.contains.append(source)
        ancestry.entities.append(contained_by)

        clean(ancestry)

        self.assertEqual(source, ancestry.entities[Source][source.id])
        self.assertIn(source, contained_by.contains)
        self.assertEqual(contained_by, ancestry.entities[Source][contained_by.id])

    def test_clean_should_not_clean_source_with_contains(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        contains = Source('S1', 'The Source')
        contains.contained_by = source
        ancestry.entities.append(contains)

        clean(ancestry)

        self.assertEqual(source, ancestry.entities[Source][source.id])
        self.assertEqual(source, contains.contained_by)
        self.assertEqual(contains, ancestry.entities[Source][contains.id])

    def test_clean_should_not_clean_source_with_files(self) -> None:
        ancestry = Ancestry()

        file = File('F0', __file__)
        ancestry.entities.append(file)

        source = Source('S0', 'The Source')
        source.files.append(file)
        ancestry.entities.append(source)

        clean(ancestry)

        self.assertEqual(source, ancestry.entities[Source][source.id])
        self.assertIn(source, file.entities)
        self.assertEqual(file, ancestry.entities[File][file.id])

    def test_clean_should_clean_citation(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The source')
        ancestry.entities.append(source)

        citation = Citation('C0', source)
        ancestry.entities.append(citation)

        clean(ancestry)

        self.assertNotIn(citation.id, ancestry.entities[Citation])
        self.assertNotIn(citation, source.citations)

    def test_clean_should_not_clean_citation_with_facts(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        citation = Citation('C0', source)
        citation.facts.append(PersonName(Person(None), 'Jane'))
        ancestry.entities.append(citation)

        fact = Person('P0')
        fact.citations.append(citation)
        ancestry.entities.append(fact)

        clean(ancestry)

        self.assertEqual(citation, ancestry.entities[Citation][citation.id])
        self.assertIn(citation, fact.citations)
        self.assertEqual(fact, ancestry.entities[Person][fact.id])

    def test_clean_should_not_clean_citation_with_files(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        file = File('F0', __file__)
        ancestry.entities.append(file)

        citation = Citation('C0', source)
        citation.files.append(file)
        ancestry.entities.append(citation)

        clean(ancestry)

        self.assertEqual(citation, ancestry.entities[Citation][citation.id])
        self.assertEqual(file, ancestry.entities[File][file.id])
        self.assertIn(citation, source.citations)
        self.assertEqual(source, ancestry.entities[Source][source.id])
