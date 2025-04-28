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

    async def test___contains__(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.mapping.ConfigurationMapping.__contains__` implementations.
        """
        configurations = await self.get_configurations()
        keys = self.get_configuration_keys()
        sut = await self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert keys[0] in sut
        assert keys[1] in sut
        assert keys[2] not in sut
        assert keys[3] not in sut


class ConfigurationMappingTestBase(
    Generic[_ConfigurationKeyT, _ConfigurationT],
    _ConfigurationMappingTestBase[_ConfigurationKeyT, _ConfigurationT],
):
    """
    A base class for testing :py:class:`betty.config.collections.mapping.ConfigurationMapping` implementations.
    """


class OrderedConfigurationMappingTestBase(
    Generic[_ConfigurationKeyT, _ConfigurationT],
    _ConfigurationMappingTestBase[_ConfigurationKeyT, _ConfigurationT],
):
    """
    A base class for testing :py:class:`betty.config.collections.mapping.OrderedConfigurationMapping` implementations.
    """
