"""
Test utilities for :py:mod:`betty.copyright_notice`.
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
    from betty.copyright_notice import CopyrightNotice


class CopyrightNoticeDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.copyright_notice.CopyrightNoticeDefinition` implementations.
    """


class CopyrightNoticeTestBase:
    """
    A base class for testing :py:class:`betty.copyright_notice.CopyrightNotice` implementations.
    """

    @pytest.fixture
    def sut(self) -> CopyrightNotice:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

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
