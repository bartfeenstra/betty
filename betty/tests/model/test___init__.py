from typing import Sequence

import pytest
from typing_extensions import override

from betty.json.schema import Schema
from betty.locale.localizable import Localizable, plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.model import (
    Entity,
    persistent_id,
    ToOneSchema,
    ToManySchema,
    ToZeroOrOneSchema,
)
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase
from betty.test_utils.model import DummyEntity
from betty.warnings import BettyDeprecationWarning


@pytest.mark.parametrize(
    ("expected", "entity"),
    [
        (False, DummyEntity()),
        (True, DummyEntity("my-first-entity-id")),
    ],
)
def test_persistent_id(expected: bool, entity: Entity) -> None:
    assert persistent_id(entity) == expected


class TestEntity:
    @pytest.mark.parametrize(
        "count",
        range(0, 9),
    )
    def test_plugin_label_count(self, count: int) -> None:
        class _Entity(Entity):
            @override
            @classmethod
            def plugin_id(cls) -> MachineName:
                return cls.__name__

            @override
            @classmethod
            def plugin_label(cls) -> Localizable:
                return plain(cls.__name__)

            @override
            @classmethod
            def plugin_label_plural(cls) -> Localizable:
                return plain(cls.__name__)

        with pytest.warns(BettyDeprecationWarning):
            assert _Entity().plugin_label_count(count).localize(DEFAULT_LOCALIZER)


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
