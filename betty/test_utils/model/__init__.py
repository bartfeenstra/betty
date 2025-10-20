"""
Test utilities for :py:mod:`betty.model`.
"""

from __future__ import annotations

from typing import final

import pytest

from betty.locale.localizable import CountablePlain, Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import Entity, EntityDefinition
from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
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


class EntityDefinitionTestBase(
    CountableHumanFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.model.EntityDefinition` implementations.
    """


@final
@EntityDefinition(
    id="dummy-one",
    label=Plain("Dummy (one)"),
    label_plural=Plain("Dummies (one)"),
    label_countable=CountablePlain("{count} dummy (one)", "{count} dummies (one)"),
)
class DummyEntityOne(Entity):
    """
    A dummy entity.
    """


@final
@EntityDefinition(
    id="dummy",
    label=Plain("Dummy (two)"),
    label_plural=Plain("Dummies (two)"),
    label_countable=CountablePlain("{count} dummy (two)", "{count} dummies (two)"),
)
class DummyEntityTwo(Entity):
    """
    A dummy entity.
    """


@final
@EntityDefinition(
    id="dummy-non-public-facing-one",
    label=Plain("Dummy non-public-facing (two)"),
    label_plural=Plain("Dummies non-public-facing (two)"),
    label_countable=CountablePlain(
        "{count} dummy non-public-facing (two)",
        "{count} dummies non-public-facing (two)",
    ),
    public_facing=False,
)
class DummyNonPublicFacingEntityOne(Entity):
    """
    A dummy non-public-facing entity.
    """
