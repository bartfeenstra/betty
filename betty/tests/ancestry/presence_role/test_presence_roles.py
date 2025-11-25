import pytest
from typing_extensions import override

from betty.ancestry.presence_role.presence_roles import (
    Attendee,
    Beneficiary,
    Celebrant,
    Informant,
    Organizer,
    Speaker,
    Subject,
    Unknown,
    Witness,
)
from betty.plugin import PluginDefinition
from betty.test_utils.ancestry.presence_role import PresenceRolePluginTestBase


class TestAttendee(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Attendee.plugin


class TestBeneficiary(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Beneficiary.plugin


class TestCelebrant(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Celebrant.plugin


class TestInformant(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Informant.plugin


class TestOrganizer(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Organizer.plugin


class TestSpeaker(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Speaker.plugin


class TestSubject(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Subject.plugin


class TestUnknown(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin


class TestWitness(PresenceRolePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Witness.plugin
