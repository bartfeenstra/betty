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
    CountableUserFacingPluginDefinitionTestBase,
)
from betty.user import UserFacing


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
    CountableUserFacingPluginDefinitionTestBase,
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
    id="dummy-user-facing-one",
    label=Plain("Dummy user-facing (two)"),
    label_plural=Plain("Dummies user-facing (two)"),
    label_countable=CountablePlain(
        "{count} dummy user-facing (two)", "{count} dummies user-facing (two)"
    ),
)
class DummyUserFacingEntityOne(UserFacing, Entity):
    """
    A dummy user-facing entity.
    """
