from __future__ import annotations

from betty.entity import Entity, EntityDefinition, resolve
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.locale.localizable import dummy_countable_localizable


class TestEntityDefinition:
    def test_public_facing(self) -> None:
        sut = EntityDefinition(
            "-dummy",
            public_facing=True,
            label="-",
            label_plural="-",
            label_countable=dummy_countable_localizable,
        )
        assert sut.public_facing


def test_resolve__with_entity() -> None:
    entity = DummyEntityOne()
    assert resolve(entity) is entity


def test_resolve__with_resolver_without_arguments() -> None:
    entity = DummyEntityOne()
    assert resolve(lambda: entity) is entity


def test_resolve__with_resolver_with_project() -> None:
    entity = DummyEntityOne()

    def resolver() -> Entity:
        return entity

    assert resolve(resolver) is entity
