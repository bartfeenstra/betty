from typing import Sequence

import pytest
from typing_extensions import override

from betty.json.schema import Schema
from betty.model import (
    EntityReferenceSchema,
    EntityReferenceCollectionSchema,
    Entity,
    persistent_id,
)
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase
from betty.test_utils.model import DummyEntity


class TestPersistentId:
    @pytest.mark.parametrize(
        ("expected", "entity"),
        [
            (False, DummyEntity()),
            (True, DummyEntity("my-first-entity-id")),
        ],
    )
    def test(self, expected: bool, entity: Entity) -> None:
        assert persistent_id(entity) == expected


class TestEntityReferenceSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                EntityReferenceSchema(),
                [
                    "https://example.com",
                ],
                [True, False, None, 123, [], {}],
            ),
        ]


class TestEntityReferenceCollectionSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                EntityReferenceCollectionSchema(),
                [
                    [],
                    ["https://example.com"],
                ],
                [True, False, None, "123", 123, {}],
            ),
        ]
