"""
Test utilities for :py:mod:`betty.config.collections.mapping`.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from typing_extensions import override

from betty.config import Configuration
from betty.config.collections import ConfigurationKey
from betty.test_utils.config.collections import ConfigurationCollectionTestBase

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)


class _ConfigurationMappingTestBase(
    Generic[_ConfigurationKeyT, _ConfigurationT],
    ConfigurationCollectionTestBase[_ConfigurationKeyT, _ConfigurationT],
):
    @override
    async def test___iter__(self) -> None:
        configurations = await self.get_configurations()
        sut = await self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert list(iter(sut)) == [
            self.get_configuration_keys()[0],
            self.get_configuration_keys()[1],
        ]


class ConfigurationMappingTestBase(
    Generic[_ConfigurationKeyT, _ConfigurationT],
    _ConfigurationMappingTestBase[_ConfigurationKeyT, _ConfigurationT],
):
    """
    A base class for testing :py:class:`betty.config.collections.mapping.ConfigurationMapping` implementations.
    """

    pass


class OrderedConfigurationMappingTestBase(
    Generic[_ConfigurationKeyT, _ConfigurationT],
    _ConfigurationMappingTestBase[_ConfigurationKeyT, _ConfigurationT],
):
    """
    A base class for testing :py:class:`betty.config.collections.mapping.OrderedConfigurationMapping` implementations.
    """

    pass
