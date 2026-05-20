from __future__ import annotations

from typing import TYPE_CHECKING

from betty.entity import Entity, EntityDefinition, resolve
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE

if TYPE_CHECKING:
    from betty.project import Project


class TestEntityDefinition:
    def test_public_facing(self) -> None:
        sut = EntityDefinition(
            "-dummy",
            public_facing=True,
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.public_facing


def test_resolve__with_entity(isolated_project: Project) -> None:
    entity = DummyEntityOne()
    assert resolve(isolated_project, entity) is entity


def test_resolve__with_resolver_without_arguments(isolated_project: Project) -> None:
    entity = DummyEntityOne()
    assert resolve(isolated_project, lambda: entity) is entity


def test_resolve__with_resolver_with_project(isolated_project: Project) -> None:
    entity = DummyEntityOne()

    def resolver(project: Project) -> Entity:
        assert project is isolated_project
        return entity

    assert resolve(isolated_project, resolver) is entity
