"""
Test utilities for :py:mod:`betty.config.collections.mapping`.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from typing_extensions import override

from betty.config import Configuration
from betty.config.collections import ConfigurationKey
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBase,
    ConfigurationCollectionTestBaseNewSut,
    ConfigurationCollectionTestBaseSutConfigurationKeys,
    ConfigurationCollectionTestBaseSutConfigurations,
)

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)


class _ConfigurationMappingTestBase(
    Generic[_ConfigurationKeyT, _ConfigurationT],
    ConfigurationCollectionTestBase[_ConfigurationKeyT, _ConfigurationT],
):
    @override
    async def test___iter__(  # type: ignore[override]
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationT, _ConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationT
        ],
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            _ConfigurationKeyT
        ],
    ) -> None:
        sut = new_sut(
            [
                sut_configurations[0],
                sut_configurations[1],
            ]
        )
        assert list(iter(sut)) == [
            sut_configuration_keys[0],
            sut_configuration_keys[1],
        ]

    async def test___contains__(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationT, _ConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationT
        ],
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            _ConfigurationKeyT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.mapping.ConfigurationMapping.__contains__` implementations.
        """
        sut = new_sut(
            [
                sut_configurations[0],
                sut_configurations[1],
            ]
        )
        assert sut_configuration_keys[0] in sut
        assert sut_configuration_keys[1] in sut
        assert sut_configuration_keys[2] not in sut
        assert sut_configuration_keys[3] not in sut


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
