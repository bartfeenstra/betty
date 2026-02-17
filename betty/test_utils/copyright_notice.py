"""
Test utilities for :py:mod:`betty.copyright_notice`.
"""

from __future__ import annotations

import pytest

from betty.copyright_notice import CopyrightNotice
from betty.locale.localize import DEFAULT_LOCALIZER


class CopyrightNoticeTestBase[CopyrightNoticeT: CopyrightNotice]:
    """
    A base class for testing :py:class:`betty.copyright_notice.CopyrightNotice` implementations.
    """

    @pytest.fixture
    def sut(self) -> type[CopyrightNoticeT]:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    def test_summary(self, sut: CopyrightNoticeT) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.summary` implementations.
        """
        assert sut.summary.localize(DEFAULT_LOCALIZER)

    def test_text(self, sut: CopyrightNoticeT) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.text` implementations.
        """
        assert sut.text.localize(DEFAULT_LOCALIZER)

    def test_url(self, sut: CopyrightNoticeT) -> None:
        """
        Tests :py:meth:`betty.copyright_notice.CopyrightNotice.url` implementations.
        """
        url = sut.url
        if url is not None:
            assert url.localize(DEFAULT_LOCALIZER)
