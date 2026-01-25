"""
Test utilities for :py:mod:`betty.definition.human_facing`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.locale.localize import DEFAULT_LOCALIZER

if TYPE_CHECKING:
    from betty.definition.human_facing import (
        CountableHumanFacingDefinition,
        HumanFacingDefinition,
    )


class HumanFacingDefinitionTestBase:
    """
    A base class for testing :py:class:`betty.definition.human_facing.HumanFacingDefinition` subclasses.
    """

    def test_label(self, sut: HumanFacingDefinition) -> None:
        """
        Tests the :py:attr:`betty.definition.human_facing.HumanFacingDefinition.label` value.
        """
        assert sut.label.localize(DEFAULT_LOCALIZER)

    def test_description(self, sut: HumanFacingDefinition) -> None:
        """
        Tests the :py:attr:`betty.definition.human_facing.HumanFacingDefinition.label` value.
        """
        if sut.description is not None:
            assert sut.description.localize(DEFAULT_LOCALIZER)


class CountableHumanFacingDefinitionTestBase(HumanFacingDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.definition.human_facing.CountableHumanFacingDefinition` subclasses.
    """

    def test_label_plural(self, sut: CountableHumanFacingDefinition) -> None:
        """
        Tests the :py:attr:`betty.definition.human_facing.CountableHumanFacingDefinition.label_plural` value.
        """
        assert sut.label_plural.localize(DEFAULT_LOCALIZER)

    @pytest.mark.parametrize(
        "count",
        range(9),
    )
    def test_label_countable(
        self, sut: CountableHumanFacingDefinition, count: int
    ) -> None:
        """
        Tests the :py:attr:`betty.definition.human_facing.CountableHumanFacingDefinition.label_countable` value.
        """
        assert sut.label_countable.count(count).localize(DEFAULT_LOCALIZER)
