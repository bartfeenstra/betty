"""
Test utilities for :py:mod:`betty.copyright_notice`.
"""

from __future__ import annotations

from betty.copyright_notice import CopyrightNotice
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class CopyrightNoticeDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.copyright_notice.CopyrightNoticeDefinition` implementations.
    """


class CopyrightNoticeTestBase(PluginTestBase[CopyrightNotice]):
    """
    A base class for testing :py:class:`betty.copyright_notice.CopyrightNotice` implementations.
    """

    def test_summary(self, sut: CopyrightNotice) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.summary` implementations.
        """
        assert sut.summary.localize(DEFAULT_LOCALIZER)

    def test_text(self, sut: CopyrightNotice) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.text` implementations.
        """
        assert sut.text.localize(DEFAULT_LOCALIZER)

    def test_url(self, sut: CopyrightNotice) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.url` implementations.
        """
        url = sut.url
        if url is not None:
            assert url.localize(DEFAULT_LOCALIZER)
