from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.presence import Presence
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
    Death,
    Birth,
    Adoption,
    Baptism,
    Burial,
    Conference,
    Confirmation,
    Correspondence,
    Cremation,
    Divorce,
    DivorceAnnouncement,
    Emigration,
    Engagement,
    Funeral,
    Immigration,
    Marriage,
    MarriageAnnouncement,
    Missing,
    Occupation,
    Residence,
    Retirement,
    Unknown,
    Will,
)
from betty.ancestry.person import Person
from betty.ancestry.presence_role.presence_roles import Subject
from betty.date import Date
from betty.project.config import DEFAULT_LIFETIME_THRESHOLD
from betty.test_utils.ancestry.event_type import EventTypeTestBase

if TYPE_CHECKING:
    from betty.ancestry.event_type import EventType


class TestAdoption(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Adoption


class TestBaptism(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Baptism


class TestBirth(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Birth


class TestBurial(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Burial


class TestConference(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Conference


class TestConfirmation(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Confirmation


class TestCorrespondence(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Correspondence


class TestCremation(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Cremation


class TestDeath(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Death

    async def test_may_create_may_not_for_person_without_presences(self) -> None:
        person = Person(id="P0")

        assert Death.may_create(person, DEFAULT_LIFETIME_THRESHOLD) is False

    async def test_may_create_may_not_within_lifetime_threshold(self) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Birth(),
                date=Date(1970, 1, 1),
            ),
        )

        assert Death.may_create(person, DEFAULT_LIFETIME_THRESHOLD) is False

    async def test_may_create_may_over_lifetime_threshold(self) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Birth(),
                date=Date(1, 1, 1),
            ),
        )

        assert Death.may_create(person, DEFAULT_LIFETIME_THRESHOLD) is True


class TestDivorce(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Divorce


class TestDivorceAnnouncement(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return DivorceAnnouncement


class TestEmigration(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Emigration


class TestEngagement(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Engagement


class TestFuneral(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Funeral


class TestImmigration(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Immigration


class TestMarriage(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Marriage


class TestMarriageAnnouncement(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return MarriageAnnouncement


class TestMissing(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Missing


class TestOccupation(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Occupation


class TestResidence(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Residence


class TestRetirement(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Retirement


class TestUnknown(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Unknown


class TestWill(EventTypeTestBase):
    @override
    def get_sut_class(self) -> type[EventType]:
        return Will
