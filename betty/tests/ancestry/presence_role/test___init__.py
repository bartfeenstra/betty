from typing import Sequence

from typing_extensions import override

from betty.ancestry.presence_role import PresenceRoleSchema
from betty.ancestry.presence_role.presence_roles import Subject
from betty.json.schema import Schema
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase


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
