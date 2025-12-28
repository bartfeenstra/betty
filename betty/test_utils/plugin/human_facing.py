"""
Test utilities for :py:mod:`betty.plugin.human_facing`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.locale.localize import DEFAULT_LOCALIZER
from betty.test_utils.plugin import PluginDefinitionTestBase

if TYPE_CHECKING:
    from betty.plugin.human_facing import (
        CountableHumanFacingPluginDefinition,
        HumanFacingPluginDefinition,
    )


class HumanFacingPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.human_facing.HumanFacingPluginDefinition` subclasses.
    """

    def test_label(self, sut: HumanFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.human_facing.HumanFacingPluginDefinition.label` value.
        """
        assert sut.label.localize(DEFAULT_LOCALIZER)

    def test_description(self, sut: HumanFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.human_facing.HumanFacingPluginDefinition.label` value.
        """
        if sut.description is not None:
            assert sut.description.localize(DEFAULT_LOCALIZER)


class CountableHumanFacingPluginDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.human_facing.CountableHumanFacingPluginDefinition` subclasses.
    """

    def test_label_plural(self, sut: CountableHumanFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.human_facing.CountableHumanFacingPluginDefinition.label_plural` value.
        """
        assert sut.label_plural.localize(DEFAULT_LOCALIZER)

    @pytest.mark.parametrize(
        "count",
        range(9),
    )
    def test_label_countable(
        self, sut: CountableHumanFacingPluginDefinition, count: int
    ) -> None:
        """
        Tests the :py:attr:`betty.plugin.human_facing.CountableHumanFacingPluginDefinition.label_countable` value.
        """
        assert sut.label_countable.count(count).localize(DEFAULT_LOCALIZER)
