from collections.abc import Sequence

import pytest
from typing_extensions import override

from betty.json.schema import Schema
from betty.locale.localizable import CountablePlain, Plain
from betty.model import (
    Entity,
    EntityDefinition,
    ToManySchema,
    ToOneSchema,
    ToZeroOrOneSchema,
    persistent_id,
)
from betty.plugin import PluginDefinition
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestEntityDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return EntityDefinition

    def test_public_facing(self) -> None:
        sut = EntityDefinition(
            public_facing=True,
            id="-",
            label=Plain(""),
            label_plural=Plain(""),
            label_countable=CountablePlain("", ""),
        )
        assert sut.public_facing


@pytest.mark.parametrize(
    ("expected", "entity"),
    [
        (False, Entity()),
        (True, Entity("my-first-entity-id")),
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
