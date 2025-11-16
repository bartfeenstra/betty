from collections.abc import Iterable
from typing import cast

import pytest
from typing_extensions import override

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
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestEntityDefinition(ClassedPluginDefinitionClassTestBase):
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
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        return [
            (
                ToOneSchema(),
                [
                    "https://example.com",
                ],
                [True, False, None, 123, [], {}],
            ),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)


class TestToZeroOrOneSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
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

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)


class TestToManySchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
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

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)
