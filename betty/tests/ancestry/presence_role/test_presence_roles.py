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
from betty.test_utils.ancestry.presence_role import PresenceRoleDefinitionTestBase


class TestAttendee(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Attendee.plugin


class TestBeneficiary(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Beneficiary.plugin


class TestCelebrant(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Celebrant.plugin


class TestInformant(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Informant.plugin


class TestOrganizer(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Organizer.plugin


class TestSpeaker(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Speaker.plugin


class TestSubject(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Subject.plugin


class TestUnknown(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin


class TestWitness(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Witness.plugin
