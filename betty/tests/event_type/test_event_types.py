from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.date import Date
from betty.event_type.event_types import (
    Adoption,
    Baptism,
    BarMitzvah,
    BatMitzvah,
    Birth,
    Burial,
    Conference,
    Confirmation,
    Correspondence,
    Cremation,
    Death,
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
from betty.presence_role.presence_roles import Subject
from betty.project import Project
from betty.test_utils.ancestry.event_type import (
    EventTypeDefinitionTestBase,
    EventTypeTestBase,
)

if TYPE_CHECKING:
    from betty.app import App
    from betty.event_type import EventType
    from betty.plugin import PluginDefinition


class TestAdoptionDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Adoption.plugin()


class TestAdoption(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Adoption()


class TestBaptismDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Baptism.plugin()


class TestBaptism(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Baptism()


class TestBarMitzvahDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return BarMitzvah.plugin()


class TestBarMitzvah(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return BarMitzvah()


class TestBatMitzvahDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return BatMitzvah.plugin()


class TestBatMitzvah(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return BatMitzvah()


class TestBirthDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Birth.plugin()


class TestBirth(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Birth()


class TestBurialDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Burial.plugin()


class TestBurial(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Burial()


class TestConferenceDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Conference.plugin()


class TestConference(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Conference()


class TestConfirmationDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Confirmation.plugin()


class TestConfirmation(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Confirmation()


class TestCorrespondenceDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Correspondence.plugin()


class TestCorrespondence(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Correspondence()


class TestCremationDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Cremation.plugin()


class TestCremation(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Cremation()


class TestDeathDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Death.plugin()


class TestDeath(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Death()

    async def test_may_create_may_not_for_person_without_presences(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            person = Person(id="P0")

            assert await Death.should_exist(project, person) is False

    async def test_may_create_may_not_within_lifetime_threshold(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Birth(),
                    date=Date(1970, 1, 1),
                ),
            )

            assert await Death.should_exist(project, person) is False

    async def test_may_create_may_over_lifetime_threshold(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Birth(),
                    date=Date(1, 1, 1),
                ),
            )

            assert await Death.should_exist(project, person) is True


class TestDivorceDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Divorce.plugin()


class TestDivorce(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Divorce()


class TestDivorceAnnouncementDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return DivorceAnnouncement.plugin()


class TestDivorceAnnouncement(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return DivorceAnnouncement()


class TestEmigrationDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Emigration.plugin()


class TestEmigration(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Emigration()


class TestEngagementDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Engagement.plugin()


class TestEngagement(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Engagement()


class TestFuneralDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Funeral.plugin()


class TestFuneral(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Funeral()


class TestImmigrationDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Immigration.plugin()


class TestImmigration(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Immigration()


class TestMarriageDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Marriage.plugin()


class TestMarriage(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Marriage()


class TestMarriageAnnouncementDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return MarriageAnnouncement.plugin()


class TestMarriageAnnouncement(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return MarriageAnnouncement()


class TestMissingDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Missing.plugin()


class TestMissing(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Missing()


class TestOccupationDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Occupation.plugin()


class TestOccupation(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Occupation()


class TestResidenceDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Residence.plugin()


class TestResidence(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Residence()


class TestRetirementDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Retirement.plugin()


class TestRetirement(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Retirement()


class TestUnknownDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin()


class TestUnknown(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Unknown()


class TestWillDefinition(EventTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Will.plugin()


class TestWill(EventTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> EventType:
        return Will()
