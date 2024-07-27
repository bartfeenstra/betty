"""
Test utilities for :py:module:`betty.config.collections.sequence`.
"""

from __future__ import annotations

from typing import Generic, TypeVar
from typing_extensions import override

from betty.config import Configuration
from betty.test_utils.config.collections import ConfigurationCollectionTestBase

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ConfigurationSequenceTestBase(
    Generic[_ConfigurationT], ConfigurationCollectionTestBase[int, _ConfigurationT]
):
    """
    A base class for testing :py:class:`betty.config.collections.sequence.ConfigurationSequence` implementations.
    """

    @override
    def get_configuration_keys(self) -> tuple[int, int, int, int]:
        return 0, 1, 2, 3

    @override
    async def test___iter__(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert [configurations[0], configurations[1]] == list(iter(sut))
