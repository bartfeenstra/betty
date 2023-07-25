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
        ancestry.add(onymous_event)

        anonymous_event = Event('E1', Birth)
        ancestry.add(anonymous_event)

        onymous_place = Place('P0', [PlaceName('Amsterdam')])
        onymous_place.events.add(onymous_event)
        ancestry.add(onymous_place)

        anonymous_place = Place('P1', [PlaceName('Almelo')])
        ancestry.add(anonymous_place)

        onymous_place_because_encloses_onymous_places = Place(
            'P3', [PlaceName('Netherlands')])
        Enclosure(onymous_place, onymous_place_because_encloses_onymous_places)
        Enclosure(anonymous_place, onymous_place_because_encloses_onymous_places)
        ancestry.add(onymous_place_because_encloses_onymous_places)

        clean(ancestry)

        assert [onymous_event] == list(ancestry[Event])
        assert [onymous_place == onymous_place_because_encloses_onymous_places], list(ancestry[Place])

        assert anonymous_place not in onymous_place_because_encloses_onymous_places.encloses

    def test_clean_should_not_clean_person_if_public(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        person.private = False
        ancestry.add(person)

        clean(ancestry)

        assert person == ancestry[Person][person.id]

    def test_clean_should_clean_person_with_private_children(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        person.private = True
        ancestry.add(person)
        child = Person('P1')
        child.private = True
        ancestry.add(child)
        grandchild = Person('P2')
        grandchild.private = True
        ancestry.add(grandchild)
        great_grandchild = Person('P3')
        great_grandchild.private = True
        ancestry.add(great_grandchild)

        clean(ancestry)

        assert person.id not in ancestry[Person]

    def test_clean_should_not_clean_person_with_public_children(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        person.private = False
        ancestry.add(person)
        child = Person('P1')
        child.private = True
        ancestry.add(child)
        grandchild = Person('P2')
        grandchild.private = True
        ancestry.add(grandchild)
        great_grandchild = Person('P3')
        great_grandchild.private = False
        ancestry.add(great_grandchild)

        clean(ancestry)

        assert person == ancestry[Person][person.id]

    def test_clean_should_clean_event(self) -> None:
        ancestry = Ancestry()

        source = Source('S1', 'The Source')
        ancestry.add(source)

        citation = Citation('C1', source)
        ancestry.add(citation)

        file = File('F1', Path(__file__))
        ancestry.add(file)

        place = Place('P0', [PlaceName('The Place')])
        ancestry.add(place)

        event = Event('E0', Birth)
        event.citations.add(citation)
        event.files.add(file)
        event.place = place
        ancestry.add(event)

        clean(ancestry)

        assert event.id not in ancestry[Event]
        assert event.place is None
        assert event not in place.events
        assert place.id not in ancestry[Place]
        assert event not in citation.facts
        assert citation.id not in ancestry[Citation]
        assert event not in file.entities
        assert file.id not in ancestry[File]

    def test_clean_should_not_clean_event_with_presences_with_people(self) -> None:
        ancestry = Ancestry()

        source = Source('S1', 'The Source')
        ancestry.add(source)

        citation = Citation('C1', source)
        ancestry.add(citation)

        file = File('F1', Path(__file__))
        ancestry.add(file)

        place = Place('P0', [PlaceName('The Place')])
        ancestry.add(place)

        person = Person('P0')

        event = Event('E0', Birth)
        event.citations.add(citation)
        event.files.add(file)
        event.place = place
        ancestry.add(event)

        Presence(person, Subject(), event)

        clean(ancestry)

        assert event == ancestry[Event][event.id]
        assert event in place.events
        assert place == ancestry[Place][place.id]
        assert event in citation.facts
        assert citation == ancestry[Citation][citation.id]
        assert event in file.entities
        assert file == ancestry[File][file.id]

    def test_clean_should_clean_file(self) -> None:
        ancestry = Ancestry()

        file = File('F0', Path(__file__))
        ancestry.add(file)

        clean(ancestry)

        assert file.id not in ancestry[File]

    def test_clean_should_not_clean_file_with_entities(self) -> None:
        ancestry = Ancestry()

        person = Person('P0')
        ancestry.add(person)

        file = File('F0', Path(__file__))
        file.entities.add(person)
        ancestry.add(file)

        clean(ancestry)

        assert file == ancestry[File][file.id]
        assert person in file.entities
        assert person == ancestry[Person][person.id]

    def test_clean_should_not_clean_file_with_citations(self) -> None:
        ancestry = Ancestry()

        source = Source(None)

        citation = Citation('C1', source)
        ancestry.add(citation)

        file = File('F0', Path(__file__))
        file.citations.add(citation)
        ancestry.add(file)

        clean(ancestry)

        assert file == ancestry[File][file.id]
        assert citation in file.citations
        assert citation == ancestry[Citation][citation.id]

    def test_clean_should_clean_source(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The source')
        ancestry.add(source)

        clean(ancestry)

        assert source.id not in ancestry[Source]

    def test_clean_should_not_clean_source_with_citations(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.add(source)

        citation = Citation('C0', source)
        citation.facts.add(PersonName(Person(None), 'Jane'))
        ancestry.add(citation)

        clean(ancestry)

        assert source == ancestry[Source][source.id]
        assert source == citation.source
        assert citation == ancestry[Citation][citation.id]

    def test_clean_should_not_clean_source_with_contained_by(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.add(source)

        contained_by = Source('S1', 'The Source')
        contained_by.contains.add(source)
        ancestry.add(contained_by)

        clean(ancestry)

        assert source == ancestry[Source][source.id]
        assert source in contained_by.contains
        assert contained_by == ancestry[Source][contained_by.id]

    def test_clean_should_not_clean_source_with_contains(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.add(source)

        contains = Source('S1', 'The Source')
        contains.contained_by = source
        ancestry.add(contains)

        clean(ancestry)

        assert source == ancestry[Source][source.id]
        assert source == contains.contained_by
        assert contains == ancestry[Source][contains.id]

    def test_clean_should_not_clean_source_with_files(self) -> None:
        ancestry = Ancestry()

        file = File('F0', Path(__file__))
        ancestry.add(file)

        source = Source('S0', 'The Source')
        source.files.add(file)
        ancestry.add(source)

        clean(ancestry)

        assert source == ancestry[Source][source.id]
        assert source in file.entities
        assert file == ancestry[File][file.id]

    def test_clean_should_clean_citation(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The source')
        ancestry.add(source)

        citation = Citation('C0', source)
        ancestry.add(citation)

        clean(ancestry)

        assert citation.id not in ancestry[Citation]
        assert citation not in source.citations

    def test_clean_should_not_clean_citation_with_facts(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.add(source)

        citation = Citation('C0', source)
        citation.facts.add(PersonName(Person(None), 'Jane'))
        ancestry.add(citation)

        fact = Person('P0')
        fact.citations.add(citation)
        ancestry.add(fact)

        clean(ancestry)

        assert citation == ancestry[Citation][citation.id]
        assert citation in fact.citations
        assert fact == ancestry[Person][fact.id]

    def test_clean_should_not_clean_citation_with_files(self) -> None:
        ancestry = Ancestry()

        source = Source('S0', 'The Source')
        ancestry.add(source)

        file = File('F0', Path(__file__))
        ancestry.add(file)

        citation = Citation('C0', source)
        citation.files.add(file)
        ancestry.add(citation)

        clean(ancestry)

        assert citation == ancestry[Citation][citation.id]
        assert file == ancestry[File][file.id]
        assert citation in source.citations
        assert source == ancestry[Source][source.id]
