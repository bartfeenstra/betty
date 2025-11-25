from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
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
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.date import Date
from betty.project import Project
from betty.test_utils.ancestry.event_type import EventTypePluginTestBase

if TYPE_CHECKING:
    from betty.app import App
    from betty.plugin import PluginDefinition


class TestAdoption(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Adoption.plugin


class TestBaptism(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Baptism.plugin


class TestBarMitzvah(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return BarMitzvah.plugin


class TestBatMitzvah(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return BatMitzvah.plugin


class TestBirth(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Birth.plugin


class TestBurial(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Burial.plugin


class TestConference(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Conference.plugin


class TestConfirmation(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Confirmation.plugin


class TestCorrespondence(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Correspondence.plugin


class TestCremation(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Cremation.plugin


class TestDeath(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Death.plugin

    async def test_may_create_may_not_for_person_without_presences(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            person = Person(id="P0")

            assert await Death.should_exist(project, person) is False

    async def test_may_create_may_not_within_lifetime_threshold(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
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
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
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


class TestDivorce(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Divorce.plugin


class TestDivorceAnnouncement(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return DivorceAnnouncement.plugin


class TestEmigration(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Emigration.plugin


class TestEngagement(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Engagement.plugin


class TestFuneral(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Funeral.plugin


class TestImmigration(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Immigration.plugin


class TestMarriage(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Marriage.plugin


class TestMarriageAnnouncement(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return MarriageAnnouncement.plugin


class TestMissing(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Missing.plugin


class TestOccupation(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Occupation.plugin


class TestResidence(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Residence.plugin


class TestRetirement(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Retirement.plugin


class TestUnknown(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin


class TestWill(EventTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Will.plugin
