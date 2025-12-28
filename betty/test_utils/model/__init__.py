"""
Test utilities for :py:mod:`betty.model`.
"""

from __future__ import annotations

from typing import final

from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.static import CountableStaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.model import Entity, EntityDefinition
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import (
    CountableHumanFacingPluginDefinitionTestBase,
)


class EntityTestBase(PluginTestBase[Entity]):
    """
    A base class for testing :py:class:`betty.model.Entity` implementations.
    """

    async def test_label(self, sut: Entity) -> None:
        """
        Tests :py:meth:`betty.model.Entity.label` implementations.
        """
        assert sut.label.localize(DEFAULT_LOCALIZER)


class EntityDefinitionTestBase(CountableHumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.model.EntityDefinition` implementations.
    """


@final
@EntityDefinition(
    "dummy-one",
    label="Dummy (one)",
    label_plural="Dummies (one)",
    label_countable=CountableStaticTranslations(
        {
            DEFAULT_LOCALE: {
                "one": "{count} dummy (one)",
                "other": "{count} dummies (one)",
            }
        }
    ),
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
    label_countable=CountableStaticTranslations(
        {
            DEFAULT_LOCALE: {
                "one": "{count} dummy (two)",
                "other": "{count} dummies (two)",
            }
        }
    ),
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
    label_countable=CountableStaticTranslations(
        {
            DEFAULT_LOCALE: {
                "one": "{count} dummy (three)",
                "other": "{count} dummies (three)",
            }
        }
    ),
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
    label_countable=CountableStaticTranslations(
        {
            DEFAULT_LOCALE: {
                "one": "{count} dummy (four)",
                "other": "{count} dummies (four)",
            }
        }
    ),
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
    label_countable=CountableStaticTranslations(
        {
            DEFAULT_LOCALE: {
                "one": "{count} dummy non-public-facing (one)",
                "other": "{count} dummies non-public-facing (one)",
            }
        }
    ),
    public_facing=False,
)
class DummyNonPublicFacingEntityOne(Entity):
    """
    A dummy non-public-facing entity.
    """
