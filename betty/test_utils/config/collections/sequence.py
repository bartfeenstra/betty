"""
Test utilities for :py:mod:`betty.config.collections.sequence`.
"""

from __future__ import annotations

from typing import Generic, TypeVar

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


class ConfigurationSequenceTestBase(
    Generic[_ConfigurationT], ConfigurationCollectionTestBase[int, _ConfigurationT]
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
    def test___iter__(  # type: ignore[override]
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[_ConfigurationT, int],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationT
        ],
    ) -> None:
        sut = new_sut(
            [
                sut_configurations[0],
                sut_configurations[1],
            ]
        )
        assert list(iter(sut)) == [sut_configurations[0], sut_configurations[1]]

    def test___contains__(
        self,
        new_sut: ConfigurationCollectionTestBaseNewSut[_ConfigurationT, int],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            _ConfigurationT
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
