"""
Test utilities for :py:mod:`betty.config.collections`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Generic, TypeAlias, TypeVar

import pytest

from betty.config import Configuration
from betty.config.collections import ConfigurationCollection, ConfigurationKey
from betty.test_utils.config import ConfigurationTestBase

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationValueT = TypeVar("_ConfigurationValueT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)
_ResolvableConfigurationKeyT = TypeVar("_ResolvableConfigurationKeyT")

ConfigurationCollectionTestBaseNewSut: TypeAlias = Callable[
    [Iterable[_ConfigurationValueT]],
    ConfigurationCollection[
        _ConfigurationKeyT, _ResolvableConfigurationKeyT, _ConfigurationValueT
    ],
]

ConfigurationCollectionTestBaseSutConfigurationKeys: TypeAlias = tuple[
    _ConfigurationKeyT, _ConfigurationKeyT, _ConfigurationKeyT, _ConfigurationKeyT
]

ConfigurationCollectionTestBaseSutConfigurations: TypeAlias = tuple[
    _ConfigurationValueT,
    _ConfigurationValueT,
    _ConfigurationValueT,
    _ConfigurationValueT,
]


class ConfigurationCollectionTestBase(
    ConfigurationTestBase[_ConfigurationT],
    Generic[
        _ConfigurationT,
        _ConfigurationKeyT,
        _ResolvableConfigurationKeyT,
        _ConfigurationValueT,
    ],
):
    """
    A base class for testing :py:class:`betty.config.collections.ConfigurationCollection` implementations.
    """

    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
    ]:
        """
        Provide a factory for the system(s) under test.
        """
        raise NotImplementedError

    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[_ConfigurationKeyT]:
        """
        Provide configuration keys for the system(s) under test.
        """
        raise NotImplementedError

    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[_ConfigurationValueT]:
        """
        Provide configurations for the system(s) under test.
        """
        raise NotImplementedError

    @pytest.fixture
    def sut(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
    ) -> ConfigurationCollection[
        _ConfigurationKeyT, _ResolvableConfigurationKeyT, _ConfigurationValueT
    ]:
        """
        Provide the system(s) under test.
        """
        return new_sut(())

    def test_replace__without_items(
        self,
        sut: ConfigurationCollection[
            _ConfigurationKeyT, _ResolvableConfigurationKeyT, _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.replace` implementations.
        """
        sut.clear()
        assert len(sut) == 0
        sut.replace()
        assert len(sut) == 0

    def test_replace__with_items(
        self,
        sut: ConfigurationCollection[
            _ConfigurationKeyT, _ResolvableConfigurationKeyT, _ConfigurationValueT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.replace` implementations.
        """
        sut.clear()
        assert len(sut) == 0
        sut.replace(*sut_configurations)
        assert len(sut) == len(sut_configurations)

    def test___getitem__(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
        sut: ConfigurationCollection[
            _ConfigurationKeyT, _ResolvableConfigurationKeyT, _ConfigurationValueT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.__getitem__` implementations.
        """
        configuration = sut_configurations[0]
        sut = new_sut([configuration])
        assert list(sut.values()) == [configuration]

    def test_keys(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            _ConfigurationKeyT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.keys` implementations.
        """
        sut = new_sut(sut_configurations)
        assert list(sut.keys()) == [*sut_configuration_keys]

    def test_values(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.values` implementations.
        """
        sut = new_sut(sut_configurations)
        assert list(sut.values()) == [*sut_configurations]

    def test___delitem__(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            _ConfigurationKeyT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.__delitem__` implementations.
        """
        configuration = sut_configurations[0]
        sut = new_sut([configuration])
        del sut[sut_configuration_keys[0]]
        assert list(sut.values()) == []

    def test___iter__(self) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.__iter__` implementations.
        """
        raise NotImplementedError

    def test___len__(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.__len__` implementations.
        """
        sut = new_sut(
            [
                sut_configurations[0],
                sut_configurations[1],
            ]
        )
        assert len(sut) == 2

    def test_prepend(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.prepend` implementations.
        """
        sut = new_sut(
            [
                sut_configurations[1],
            ]
        )
        sut.prepend(sut_configurations[0])
        assert list(sut.values()) == [sut_configurations[0], sut_configurations[1]]

    def test_append(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.append` implementations.
        """
        sut = new_sut(
            [
                sut_configurations[0],
            ]
        )
        sut.append(sut_configurations[1], sut_configurations[2])
        assert [
            sut_configurations[0],
            sut_configurations[1],
            sut_configurations[2],
        ] == list(sut.values())

    def test_insert(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[
            _ConfigurationValueT, _ConfigurationKeyT, _ResolvableConfigurationKeyT
        ],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.ConfigurationCollection.insert` implementations.
        """
        sut = new_sut(
            [
                sut_configurations[0],
                sut_configurations[1],
            ]
        )
        sut.insert(1, sut_configurations[2], sut_configurations[3])
        assert list(sut.values()) == [
            sut_configurations[0],
            sut_configurations[2],
            sut_configurations[3],
            sut_configurations[1],
        ]
