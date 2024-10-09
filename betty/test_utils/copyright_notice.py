"""
Test utilities for :py:mod:`betty.copyright_notice`.
"""

from __future__ import annotations

from typing_extensions import override

from betty.copyright_notice import CopyrightNotice
from betty.locale.localizable import Localizable, plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.plugin import (
    DummyPlugin,
    PluginInstanceTestBase,
)


class CopyrightNoticeTestBase(PluginInstanceTestBase[CopyrightNotice]):
    """
    A base class for testing :py:class:`betty.copyright_notice.CopyrightNotice` implementations.
    """

    def test_summary(self) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.summary` implementations.
        """
        for sut in self.get_sut_instances():
            assert sut.summary.localize(DEFAULT_LOCALIZER)

    def test_text(self) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.text` implementations.
        """
        for sut in self.get_sut_instances():
            assert sut.text.localize(DEFAULT_LOCALIZER)

    def test_url(self) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.url` implementations.
        """
        for sut in self.get_sut_instances():
            url = sut.url
            if url is not None:
                assert url.localize(DEFAULT_LOCALIZER)


class DummyCopyrightNotice(DummyPlugin, CopyrightNotice):
    """
    A dummy copyright notice implementation.
    """

    @override
    @property
    def summary(self) -> Localizable:
        return plain("Dummy Copyright Notice Summary")  # pragma: no cover

    @override
    @property
    def text(self) -> Localizable:
        return plain("Dummy Copyright Notice Text")  # pragma: no cover
