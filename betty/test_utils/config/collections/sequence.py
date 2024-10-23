"""
Test utilities for :py:mod:`betty.config.collections.sequence`.
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
        configurations = await self.get_configurations()
        sut = await self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert list(iter(sut)) == [configurations[0], configurations[1]]

    async def test___contains__(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.sequence.ConfigurationSequence.__contains__` implementations.
        """
        configurations = await self.get_configurations()
        sut = await self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert configurations[0] in sut
        assert configurations[1] in sut
        assert configurations[2] not in sut
        assert configurations[3] not in sut
