from typing_extensions import override

from betty.ancestry.presence_role import PresenceRole
from betty.ancestry.presence_role.presence_roles import (
    Subject,
    Attendee,
    Witness,
    Speaker,
    Celebrant,
    Organizer,
    Beneficiary,
    Unknown,
    Informant,
)
from betty.test_utils.plugin import PluginTestBase


class TestAttendee(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Attendee


class TestBeneficiary(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Beneficiary


class TestCelebrant(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Celebrant


class TestInformant(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Informant


class TestOrganizer(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Organizer


class TestSpeaker(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Speaker


class TestSubject(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Subject


class TestUnknown(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Unknown


class TestWitness(PluginTestBase[PresenceRole]):
    @override
    def get_sut_class(self) -> type[PresenceRole]:
        return Witness
