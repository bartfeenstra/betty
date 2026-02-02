import pytest
from typing_extensions import override

from betty.plugin import PluginDefinition
from betty.presence_role import PresenceRole
from betty.presence_role.presence_roles import (
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
from betty.test_utils.ancestry.presence_role import (
    PresenceRoleDefinitionTestBase,
    PresenceRoleTestBase,
)


class TestAttendeeDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Attendee.plugin()


class TestAttendee(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Attendee()


class TestBeneficiaryDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Beneficiary.plugin()


class TestBeneficiary(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Beneficiary()


class TestCelebrantDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Celebrant.plugin()


class TestCelebrant(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Celebrant()


class TestInformantDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Informant.plugin()


class TestInformant(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Informant()


class TestOrganizerDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Organizer.plugin()


class TestOrganizer(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Organizer()


class TestSpeakerDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Speaker.plugin()


class TestSpeaker(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Speaker()


class TestSubjectDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Subject.plugin()


class TestSubject(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Subject()


class TestUnknownDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin()


class TestUnknown(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Unknown()


class TestWitnessDefinition(PresenceRoleDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Witness.plugin()


class TestWitness(PresenceRoleTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PresenceRole:
        return Witness()
