"""
Test utilities for :py:mod:`betty.config.collections.sequence`.
"""

from __future__ import annotations

from typing import TypeVar

import pytest
from typing_extensions import override

from betty.config import Configuration
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBase,
    ConfigurationCollectionTestBaseNewSut,
    ConfigurationCollectionTestBaseSutConfigurationKeys,
    ConfigurationCollectionTestBaseSutConfigurations,
)

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationValueT = TypeVar("_ConfigurationValueT", bound=Configuration)


class ConfigurationSequenceTestBase(
    ConfigurationCollectionTestBase[_ConfigurationT, int, int, _ConfigurationValueT]
):
    """
    A base class for testing :py:class:`betty.config.collections.sequence.ConfigurationSequence` implementations.
    """

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[int]:
        return 0, 1, 2, 3

    @override
    def test___iter__(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[_ConfigurationValueT, int, int],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:  # ty:ignore[invalid-method-override]
        sut = new_sut(
            [
                sut_configurations[0],
                sut_configurations[1],
            ]
        )
        assert list(iter(sut)) == [sut_configurations[0], sut_configurations[1]]

    def test___contains__(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[_ConfigurationValueT, int, int],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationValueT
        ],
    ) -> None:
        """
        Tests :py:meth:`betty.config.collections.sequence.ConfigurationSequence.__contains__` implementations.
        """
        sut = new_sut(
            [
                sut_configurations[0],
                sut_configurations[1],
            ]
        )
        assert sut_configurations[0] in sut
        assert sut_configurations[1] in sut
        assert sut_configurations[2] not in sut
        assert sut_configurations[3] not in sut
