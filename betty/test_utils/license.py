"""
Test utilities for :py:mod:`betty.license`.
"""

from __future__ import annotations

import pytest

from betty.license import License
from betty.localizer import default_localizer


class LicenseTestBase[LicenseT: License]:
    """
    A base class for testing :py:class:`betty.license.License` implementations.
    """

    @pytest.fixture
    def sut(self) -> type[LicenseT]:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    def test_summary(self, sut: LicenseT) -> None:
        """
        Tests :py:meth:`betty.license.License.summary` implementations.
        """
        assert sut.summary.localize(default_localizer)

    def test_text(self, sut: LicenseT) -> None:
        """
        Tests :py:meth:`betty.license.License.text` implementations.
        """
        assert sut.text.localize(default_localizer)

    def test_url(self, sut: LicenseT) -> None:
        """
        Tests :py:meth:`betty.license.License.url` implementations.
        """
        url = sut.url
        if url is not None:
            assert url.localize(default_localizer)
