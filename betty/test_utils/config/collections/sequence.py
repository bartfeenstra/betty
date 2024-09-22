"""
Test utilities for :py:mod:`betty.config.collections.sequence`.
"""

from __future__ import annotations

from typing import Generic, TypeVar, TYPE_CHECKING

from typing_extensions import override

from betty.config import Configuration
from betty.test_utils.config.collections import ConfigurationCollectionTestBase

if TYPE_CHECKING:
    from betty.config.collections.sequence import ConfigurationSequence
    from collections.abc import Iterable

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ConfigurationSequenceTestBase(
    Generic[_ConfigurationT], ConfigurationCollectionTestBase[int, _ConfigurationT]
):
    """
    A base class for testing :py:class:`betty.config.collections.sequence.ConfigurationSequence` implementations.
    """

    @override
    def get_sut(
        self, configurations: Iterable[_ConfigurationT] | None = None
    ) -> ConfigurationSequence[_ConfigurationT]:
        raise NotImplementedError

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
        assert list(iter(sut)) == [configurations[0], configurations[1]]
