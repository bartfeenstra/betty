"""
Test utilities for :py:mod:`betty.license`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    HumanFacingPluginDefinitionTestBase,
)

if TYPE_CHECKING:
    from betty.license import License


class LicenseDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase, ClassedPluginDefinitionTestBase
):
    """
    A base class for testing :py:class:`betty.license.LicenseDefinition` implementations.
    """


class LicenseTestBase:
    """
    A base class for testing :py:class:`betty.license.License` implementations.
    """

    @pytest.fixture
    def sut(self) -> License:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    def test_summary(self, sut: License) -> None:
        """
        Tests :py:meth:`betty.license.License.summary` implementations.
        """
        assert sut.summary.localize(DEFAULT_LOCALIZER)

    def test_text(self, sut: License) -> None:
        """
        Tests :py:meth:`betty.license.License.text` implementations.
        """
        assert sut.text.localize(DEFAULT_LOCALIZER)

    def test_url(self, sut: License) -> None:
        """
        Tests :py:meth:`betty.license.License.url` implementations.
        """
        url = sut.url
        if url is not None:
            assert url.localize(DEFAULT_LOCALIZER)
