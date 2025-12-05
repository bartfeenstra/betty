"""
Test utilities for :py:mod:`betty.model`.
"""

from __future__ import annotations

from typing import final

import pytest

from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import CountableStaticTranslations
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import Entity, EntityPlugin
from betty.test_utils.plugin.human_facing import (
    CountableHumanFacingPluginDefinitionTestBase,
)


class EntityTestBase:
    """
    A base class for testing :py:class:`betty.model.Entity` implementations.
    """

    @pytest.fixture
    def sut(self) -> Entity:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    async def test_label(self, sut: Entity) -> None:
        """
        Tests :py:meth:`betty.model.Entity.label` implementations.
        """
        assert sut.label.localize(DEFAULT_LOCALIZER)


class EntityPluginTestBase(CountableHumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.model.EntityPlugin` implementations.
    """


@final
@EntityPlugin(
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
@EntityPlugin(
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
@EntityPlugin(
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
@EntityPlugin(
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
@EntityPlugin(
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
