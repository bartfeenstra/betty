from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from betty.date import AnyDate, Date, DateRange
from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.place import Place
from betty.entities.presence import Presence
from betty.entities.source import Source
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.event_types.unknown import UnknownEventType
from betty.privacy import Privacy
from betty.project import default_lifetime_threshold
from betty.roles.subject import Subject
from betty.roles.unknown import UnknownRole
from betty.service_providers._theme import (
    associated_file_references,
    person_timeline_events,
)
from betty.test_utils.entity.associations.has_file_references import (
    DummyHasFileReferences,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.event_type import EventType
    from betty.role import Role

__reference_date: Final[Date] = Date(1970, 1, 1)
_reference_dates: Final[Sequence[AnyDate]] = (
    __reference_date,
    DateRange(__reference_date),
    DateRange(None, __reference_date),
)
_before_reference_date: Final[Date] = Date(1900, 1, 1)
_after_reference_date: Final[Date] = Date(2000, 1, 1)


def _parameterize_with_associated_events() -> Sequence[
    tuple[
        bool,
        Role,
        str | None,
        Privacy,
        EventType,
        AnyDate | None,
        Privacy,
        EventType,
        AnyDate | None,
    ]
]:
    return tuple(__parameterize_with_associated_events())


def __parameterize_with_associated_events():  # noqa: ANN202
    ids = (
        (True, "my-first-event"),
        (False, None),
    )
    privacies = (
        (True, Privacy.PUBLIC),
        (False, Privacy.PRIVATE),
    )
    person_event_reference_resolvable_date = (
        *((True, reference_date) for reference_date in _reference_dates),
        (False, None),
    )
    person_roles = (
        (True, Subject()),
        (False, UnknownRole()),
    )
    event_types = (
        (True, Birth()),
        (False, UnknownEventType()),
    )
    event_resolvable_date_and_person_reference_event_types = (
        (True, _after_reference_date, Birth()),
        (False, _before_reference_date, Birth()),
        (True, _before_reference_date, Death()),
        (False, _after_reference_date, Death()),
    )
    for event_id_expected, event_id in ids:
        for event_privacy_expected, event_privacy in privacies:
            for (
                person_reference_event_privacy_expected,
                person_reference_event_privacy,
            ) in privacies:
                for (
                    person_reference_event_resolvable_date_expected,
                    person_reference_event_resolvable_date,
                ) in person_event_reference_resolvable_date:
                    for (
                        person_role_expected,
                        person_role,
                    ) in person_roles:
                        for (
                            event_resolvable_date_and_person_reference_event_type_expected,
                            event_resolvable_date,
                            person_reference_event_type,
                        ) in event_resolvable_date_and_person_reference_event_types:
                            for event_type_expected, event_type in event_types:
                                yield (
                                    all((
                                        person_role_expected,
                                        event_id_expected,
                                        event_privacy_expected,
                                        event_type_expected,
                                        event_resolvable_date_and_person_reference_event_type_expected,
                                        person_reference_event_privacy_expected,
                                        person_reference_event_resolvable_date_expected,
                                    )),
                                    person_role,
                                    event_id,
                                    event_privacy,
                                    event_type,
                                    event_resolvable_date,
                                    person_reference_event_privacy,
                                    person_reference_event_type,
                                    person_reference_event_resolvable_date,
                                )


class TestPersonLifetimeEvents:
    @pytest.mark.parametrize(
        ("expected", "event_id", "event_privacy", "event_date"),
        [
            # Events without dates are omitted from timelines.
            (False, "my-first-event", Privacy.PUBLIC, None),
            (True, "my-first-event", Privacy.PUBLIC, Date(1970, 1, 1)),
            # Events with generated IDs are included if they are the person's own.
            (True, None, Privacy.PUBLIC, Date(1970, 1, 1)),
            # Events with non-comparable dates are omitted from timelines.
            (False, "my-first-event", Privacy.PUBLIC, Date(None, 1, 1)),
            # Private events are omitted from timelines.
            (False, "my-first-event", Privacy.PRIVATE, Date(1970, 1, 1)),
        ],
    )
    async def test_with_person_event(
        self,
        expected: bool,
        event_id: str | None,
        event_privacy: Privacy,
        event_date: AnyDate | None,
    ) -> None:
        person = Person()
        event = Event(
            id=event_id,
            event_type=UnknownEventType(),
            date=event_date,
            privacy=event_privacy,
        )
        Presence(person, UnknownRole(), event)
        actual = list(person_timeline_events(person, default_lifetime_threshold))
        assert expected is (event in actual)

    @pytest.mark.parametrize(
        (
            "expected",
            "role",
            "event_id",
            "event_privacy",
            "event_type",
            "event_date",
            "person_reference_event_privacy",
            "person_reference_event_type",
            "person_reference_event_date",
        ),
        _parameterize_with_associated_events(),
    )
    async def test_with_associated_events(
        self,
        expected: bool,
        role: Role,
        event_id: str | None,
        event_privacy: Privacy,
        event_type: EventType,
        event_date: AnyDate | None,
        person_reference_event_privacy: Privacy,
        person_reference_event_type: EventType,
        person_reference_event_date: AnyDate | None,
    ) -> None:
        event_ids = 0

        def _event_id(event_id: str | None) -> str | None:
            nonlocal event_ids

            if event_id is None:
                return None
            event_ids += 1
            return f"{event_id}-{event_ids}"

        person = Person()
        person_reference_event = Event(
            id=_event_id(event_id),
            event_type=person_reference_event_type,
            date=person_reference_event_date,
            privacy=person_reference_event_privacy,
        )
        Presence(person, Subject(), person_reference_event)

        ancestor1 = Person()
        ancestor1.children.add(person)
        ancestor2 = Person()
        ancestor2.children.add(ancestor1)
        ancestor3 = Person()
        ancestor3.children.add(ancestor2)
        ancestor3_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_date,
            privacy=event_privacy,
        )
        Presence(ancestor3, role, ancestor3_event)

        descendant1 = Person()
        descendant1.parents.add(person)
        descendant2 = Person()
        descendant2.parents.add(descendant1)
        descendant3 = Person()
        descendant3.parents.add(descendant2)
        descendant3_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_date,
            privacy=event_privacy,
        )
        Presence(descendant3, role, descendant3_event)

        sibling = Person()
        sibling.parents.add(ancestor1)
        sibling_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_date,
            privacy=event_privacy,
        )
        Presence(sibling, role, sibling_event)

        actual = list(person_timeline_events(person, default_lifetime_threshold))
        assert expected is (ancestor3_event in actual)
        assert expected is (descendant3_event in actual)
        assert expected is (sibling_event in actual)


class TestAssociatedFileReferences:
    async def test_with_plain_has_file_references_without_files(self) -> None:
        assert list(associated_file_references(DummyHasFileReferences())) == []

    async def test_with_plain_has_file_references_with_files(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())

        has_file_references = DummyHasFileReferences()
        FileReference(has_file_references, file1)
        FileReference(has_file_references, file2)
        assert [
            file_reference.file
            for file_reference in associated_file_references(has_file_references)
        ] == [file1, file2]

    async def test_with_event_without_files(self) -> None:
        event = Event(event_type=UnknownEventType())
        assert list(associated_file_references(event)) == []

    async def test_with_event_with_citations(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())
        file3 = File(path=Path())
        file4 = File(path=Path())
        event = Event(event_type=UnknownEventType())
        FileReference(event, file1)
        FileReference(event, file2)
        FileReference(event, file1)
        citation = Citation(source=Source())
        FileReference(citation, file3)
        FileReference(citation, file4)
        FileReference(citation, file2)
        event.citations = [citation]
        assert [
            file_reference.file for file_reference in associated_file_references(event)
        ] == [file1, file2, file3, file4]

    async def test_with_person_without_files(
        self,
    ) -> None:
        person = Person(id="1")
        assert list(associated_file_references(person)) == []

    async def test_with_person_with_files(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())
        file3 = File(path=Path())
        file4 = File(path=Path())
        file5 = File(path=Path())
        file6 = File(path=Path())
        person = Person(id="1")
        FileReference(person, file1)
        FileReference(person, file2)
        FileReference(person, file1)
        citation = Citation(source=Source())
        FileReference(citation, file3)
        FileReference(citation, file4)
        FileReference(citation, file2)
        name = PersonName(
            person=person,
            individual="Janet",
        )
        name.citations = [citation]
        event = Event(event_type=UnknownEventType())
        FileReference(event, file5)
        FileReference(event, file6)
        FileReference(event, file4)
        Presence(person, Subject(), event)
        assert [
            file_reference.file for file_reference in associated_file_references(person)
        ] == [file1, file2, file3, file4, file5, file6]

    async def test_with_place_without_files(self) -> None:
        place = Place(id="1")
        assert list(associated_file_references(place)) == []

    async def test_with_place_with_files(self) -> None:
        file1 = File(path=Path())
        file2 = File(path=Path())
        file3 = File(path=Path())
        file4 = File(path=Path())
        place = Place(id="1")
        FileReference(place, file1)
        FileReference(place, file2)
        FileReference(place, file1)
        event = Event(event_type=UnknownEventType())
        FileReference(event, file3)
        FileReference(event, file4)
        FileReference(event, file4)
        event.place = place
        assert [
            file_reference.file for file_reference in associated_file_references(place)
        ] == [file1, file2, file3, file4]
