from typing import Sequence

from typing_extensions import override

from betty.ancestry.presence_role import (
    PresenceRoleSchema,
    Subject,
    PresenceRole,
    Attendee,
    Witness,
    Speaker,
    Celebrant,
    Organizer,
    Beneficiary,
    Unknown,
)
from betty.json.schema import Schema
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase
from betty.test_utils.plugin import PluginTestBase


class TestPresenceRoleSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                PresenceRoleSchema(),
                [Subject.plugin_id()],
                [True, False, None, 123, [], {}],
            )
        ]


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
