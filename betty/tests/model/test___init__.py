from collections.abc import Sequence

import pytest
from typing_extensions import override

from betty.json.schema import Schema
from betty.model import (
    Entity,
    ToManySchema,
    ToOneSchema,
    ToZeroOrOneSchema,
    persistent_id,
)
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase
from betty.test_utils.model import DummyEntity


@pytest.mark.parametrize(
    ("expected", "entity"),
    [
        (False, DummyEntity()),
        (True, DummyEntity("my-first-entity-id")),
    ],
)
def test_persistent_id(expected: bool, entity: Entity) -> None:
    assert persistent_id(entity) == expected


class TestToOneSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                ToOneSchema(),
                [
                    "https://example.com",
                ],
                [True, False, None, 123, [], {}],
            ),
        ]


class TestToZeroOrOneSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                ToZeroOrOneSchema(),
                [
                    "https://example.com",
                    None,
                ],
                [True, False, 123, [], {}],
            ),
        ]


class TestToManySchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                ToManySchema(),
                [
                    [],
                    ["https://example.com"],
                ],
                [True, False, None, "123", 123, {}],
            ),
        ]
