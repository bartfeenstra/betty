from pathlib import Path

from betty.cleaner import clean
from betty.model.ancestry import Ancestry, Person, Place, Presence, PlaceName, File, PersonName, Subject, \
    Enclosure, Source, Citation, Event
from betty.model.event_type import Birth


class TestClean:
    def test_clean(self) -> None:
        ancestry = Ancestry()

        onymous_event = Event('E0', Birth)
        Presence(Person('P0'), Subject(), onymous_event)
        ancestry.entities.append(onymous_event)

        anonymous_event = Event('E1', Birth)
        ancestry.entities.append(anonymous_event)

        onymous_place = Place('P0', [PlaceName('Amsterdam')])
        onymous_place.events.append(onymous_event)
        ancestry.entities.append(onymous_place)

        anonymous_place = Place('P1', [PlaceName('Almelo')])
        ancestry.entities.append(anonymous_place)

        onymous_place_because_encloses_onymous_places = Place(
            'P3', [PlaceName('Netherlands')])
        Enclosure(onymous_place, onymous_place_because_encloses_onymous_places)
        Enclosure(anonymous_place, onymous_place_because_encloses_onymous_places)
        ancestry.entities.append(onymous_place_because_encloses_onymous_places)

        clean(ancestry)

        assert [onymous_event] == list(ancestry.entities[Event])
        assert [onymous_place == onymous_place_because_encloses_onymous_places], list(ancestry.entities[Place])

        assert anonymous_place not in onymous_place_because_encloses_onymous_places.encloses

    def test_clean_should_not_clean_person_if_public(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        person.private = False
        ancestry.entities.append(person)

        clean(ancestry)

        assert person == ancestry.entities[Person][person.id]

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

        assert person.id not in ancestry.entities[Person]

    def test_clean_should_not_clean_person_with_public_children(self) -> None:
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

        assert person == ancestry.entities[Person][person.id]

    def test_clean_should_clean_event(self) -> None:
        ancestry = Ancestry()

        source = Source('S1', 'The Source')
        ancestry.entities.append(source)

        citation = Citation('C1', source)
        ancestry.entities.append(citation)

        file = File('F1', Path(__file__))
        ancestry.entities.append(file)

        place = Place('P0', [PlaceName('The Place')])
        ancestry.entities.append(place)

        event = Event('E0', Birth)
        event.citations.append(citation)
        event.files.append(file)
        event.place = place
        ancestry.entities.append(event)

        clean(ancestry)

        assert event.id not in ancestry.entities[Event]
        assert event.place is None
        assert event not in place.events
        assert place.id not in ancestry.entities[Place]
        assert event not in citation.facts
        assert citation.id not in ancestry.entities[Citation]
        assert event not in file.entities
        assert file.id not in ancestry.entities[File]

    def test_clean_should_not_clean_event_with_presences_with_people(self) -> None:
        ancestry = Ancestry()

        source = Source('S1', 'The Source')
        ancestry.entities.append(source)

        citation = Citation('C1', source)
        ancestry.entities.append(citation)

        file = File('F1', Path(__file__))
        ancestry.entities.append(file)

        place = Place('P0', [PlaceName('The Place')])
        ancestry.entities.append(place)

        person = Person('P0')

        event = Event('E0', Birth)
        event.citations.append(citation)
        event.files.append(file)
        event.place = place
        ancestry.entities.append(event)

        Presence(person, Subject(), event)

        clean(ancestry)

        assert event == ancestry.entities[Event][event.id]
        assert event in place.events
        assert place == ancestry.entities[Place][place.id]
        assert event in citation.facts
        assert citation == ancestry.entities[Citation][citation.id]
        assert event in file.entities
        assert file == ancestry.entities[File][file.id]

    def test_clean_should_clean_file(self) -> None:
        ancestry = Ancestry()

        file = File('F0', Path(__file__))
        ancestry.entities.append(file)

        clean(ancestry)

        assert file.id not in ancestry.entities[File]

    def test_clean_should_not_clean_file_with_entities(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        ancestry.entities.append(person)

        file = File('F0', Path(__file__))
        file.entities.append(person)
        ancestry.entities.append(file)

        clean(ancestry)

        assert file == ancestry.entities[File][file.id]
        assert person in file.entities
        assert person == ancestry.entities[Person][person.id]

    def test_clean_should_not_clean_file_with_citations(self) -> None:
        ancestry = Ancestry()

        source = Source(None)

        citation = Citation('C1', source)
        ancestry.entities.append(citation)

        file = File('F0', Path(__file__))
        file.citations.append(citation)
        ancestry.entities.append(file)

        clean(ancestry)

        assert file == ancestry.entities[File][file.id]
        assert citation in file.citations
        assert citation == ancestry.entities[Citation][citation.id]

    def test_clean_should_clean_source(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The source')
        ancestry.entities.append(source)

        clean(ancestry)

        assert source.id not in ancestry.entities[Source]

    def test_clean_should_not_clean_source_with_citations(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        citation = Citation('C0', source)
        citation.facts.append(PersonName(Person(None), 'Jane'))
        ancestry.entities.append(citation)

        clean(ancestry)

        assert source == ancestry.entities[Source][source.id]
        assert source == citation.source
        assert citation == ancestry.entities[Citation][citation.id]

    def test_clean_should_not_clean_source_with_contained_by(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        contained_by = Source('S1', 'The Source')
        contained_by.contains.append(source)
        ancestry.entities.append(contained_by)

        clean(ancestry)

        assert source == ancestry.entities[Source][source.id]
        assert source in contained_by.contains
        assert contained_by == ancestry.entities[Source][contained_by.id]

    def test_clean_should_not_clean_source_with_contains(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        contains = Source('S1', 'The Source')
        contains.contained_by = source
        ancestry.entities.append(contains)

        clean(ancestry)

        assert source == ancestry.entities[Source][source.id]
        assert source == contains.contained_by
        assert contains == ancestry.entities[Source][contains.id]

    def test_clean_should_not_clean_source_with_files(self) -> None:
        ancestry = Ancestry()

        file = File('F0', Path(__file__))
        ancestry.entities.append(file)

        source = Source('S0', 'The Source')
        source.files.append(file)
        ancestry.entities.append(source)

        clean(ancestry)

        assert source == ancestry.entities[Source][source.id]
        assert source in file.entities
        assert file == ancestry.entities[File][file.id]

    def test_clean_should_clean_citation(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The source')
        ancestry.entities.append(source)

        citation = Citation('C0', source)
        ancestry.entities.append(citation)

        clean(ancestry)

        assert citation.id not in ancestry.entities[Citation]
        assert citation not in source.citations

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

        assert citation == ancestry.entities[Citation][citation.id]
        assert citation in fact.citations
        assert fact == ancestry.entities[Person][fact.id]

    def test_clean_should_not_clean_citation_with_files(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.entities.append(source)

        file = File('F0', Path(__file__))
        ancestry.entities.append(file)

        citation = Citation('C0', source)
        citation.files.append(file)
        ancestry.entities.append(citation)

        clean(ancestry)

        assert citation == ancestry.entities[Citation][citation.id]
        assert file == ancestry.entities[File][file.id]
        assert citation in source.citations
        assert source == ancestry.entities[Source][source.id]
