"""
Test utilities for :py:mod:`betty.entity`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, final

import pytest

from betty.entity import Entity, EntityDefinition
from betty.entity.collection.multiple import MultipleTypesEntityCollection
from betty.locale import default_locale
from betty.localizables.static import CountableStaticTranslations
from betty.localizer import default_localizer

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.entity.collection import EntityCollection


class EntityTestBase[EntityT: Entity]:
    """
    A base class for testing :py:class:`betty.entity.Entity` implementations.
    """

    @pytest.fixture
    def sut(self) -> type[EntityT]:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    async def test_label(self, sut: EntityT) -> None:
        """
        Tests :py:meth:`betty.entity.Entity.label` implementations.
        """
        assert sut.label.localize(default_localizer)


@final
@EntityDefinition(
    "dummy-one",
    label="Dummy (one)",
    label_plural="Dummies (one)",
    label_countable=CountableStaticTranslations({
        default_locale: {
            "one": "{count} dummy (one)",
            "other": "{count} dummies (one)",
        }
    }),
)
class DummyEntityOne(Entity):
    """
    A dummy entity.
    """


@final
@EntityDefinition(
    "dummy",
    label="Dummy (two)",
    label_plural="Dummies (two)",
    label_countable=CountableStaticTranslations({
        default_locale: {
            "one": "{count} dummy (two)",
            "other": "{count} dummies (two)",
        }
    }),
)
class DummyEntityTwo(Entity):
    """
    A dummy entity.
    """


@final
@EntityDefinition(
    "dummy",
    label="Dummy (three)",
    label_plural="Dummies (three)",
    label_countable=CountableStaticTranslations({
        default_locale: {
            "one": "{count} dummy (three)",
            "other": "{count} dummies (three)",
        }
    }),
)
class DummyEntityThree(Entity):
    """
    A dummy entity.
    """


@final
@EntityDefinition(
    "dummy",
    label="Dummy (four)",
    label_plural="Dummies (four)",
    label_countable=CountableStaticTranslations({
        default_locale: {
            "one": "{count} dummy (four)",
            "other": "{count} dummies (four)",
        }
    }),
)
class DummyEntityFour(Entity):
    """
    A dummy entity.
    """


@final
@EntityDefinition(
    "dummy-non-public-facing-one",
    label="Dummy non-public-facing (two)",
    label_plural="Dummies non-public-facing (two)",
    label_countable=CountableStaticTranslations({
        default_locale: {
            "one": "{count} dummy non-public-facing (one)",
            "other": "{count} dummies non-public-facing (one)",
        }
    }),
    public_facing=False,
)
class DummyNonPublicFacingEntityOne(Entity):
    """
    A dummy non-public-facing entity.
    """


@contextmanager
def record_added[EntityT: Entity](
    entities: EntityCollection[EntityT], /
) -> Iterator[MultipleTypesEntityCollection[EntityT]]:
    """
    Record all entities that are added to a collection.
    """
    original = [*entities]
    added = MultipleTypesEntityCollection[EntityT]()
    yield added
    added.add(*[entity for entity in entities if entity not in original])
