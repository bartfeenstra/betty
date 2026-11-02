"""
Test utilities for :py:mod:`betty.copyright_notice`.
"""

from __future__ import annotations

import pytest

from betty.copyright_notice import CopyrightNotice
from betty.localizer import default_localizer
from betty.test_utils import AbstractMethod


class CopyrightNoticeTestBase[CopyrightNoticeT: CopyrightNotice]:
    """
    A base class for testing :py:class:`betty.copyright_notice.CopyrightNotice` implementations.
    """

    @pytest.fixture
    def sut(self) -> type[CopyrightNoticeT]:
        """
        Provide the system(s) under test.
        """
        raise AbstractMethod

    def test_summary(self, sut: CopyrightNoticeT) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.summary` implementations.
        """
        assert default_localizer.localize(sut.summary)

    def test_text(self, sut: CopyrightNoticeT) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.text` implementations.
        """
        assert default_localizer.localize(sut.text)

    def test_url(self, sut: CopyrightNoticeT) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.url` implementations.
        """
        url = sut.url
        if url is not None:
            assert default_localizer.localize(url)
