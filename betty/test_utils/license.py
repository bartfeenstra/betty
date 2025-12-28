"""
Test utilities for :py:mod:`betty.license`.
"""

from __future__ import annotations

from betty.license import License
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class LicenseDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.license.LicenseDefinition` implementations.
    """


class LicenseTestBase(PluginTestBase[License]):
    """
    A base class for testing :py:class:`betty.license.License` implementations.
    """

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
