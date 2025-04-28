"""
Test utilities for :py:mod:`betty.model`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.locale.localizable import Localizable, plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import Entity, UserFacingEntity
from betty.test_utils.plugin import DummyPlugin, PluginTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence


class EntityTestBase(PluginTestBase[Entity]):
    """
    A base class for testing :py:class:`betty.model.Entity` implementations.
    """

    async def get_sut_instances(self) -> Sequence[Entity]:
        """
        Get instances of the entity type under test.
        """
        raise NotImplementedError

    async def test_plugin_label_plural(self) -> None:
        """
        Tests :py:meth:`betty.model.Entity.plugin_label_plural` implementations.
        """
        assert self.get_sut_class().plugin_label_plural().localize(DEFAULT_LOCALIZER)

    async def test_label(self) -> None:
        """
        Tests :py:meth:`betty.model.Entity.label` implementations.
        """
        for entity in await self.get_sut_instances():
            assert entity.label.localize(DEFAULT_LOCALIZER)


class DummyEntity(DummyPlugin, Entity):
    """
    A dummy entity.
    """

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return plain(cls.__name__)

    @override
    @classmethod
    def plugin_label_count(cls, count: int) -> Localizable:
        return plain(cls.__name__)


class DummyUserFacingEntity(UserFacingEntity, DummyEntity):
    """
    A dummy user-facing entity.
    """
