"""
Test utilities for :py:mod:`betty.license`.
"""

from __future__ import annotations

from typing import Generic

import pytest
from typing_extensions import TypeVar

from betty.license import License
from betty.locale.localize import DEFAULT_LOCALIZER

_LicenseT = TypeVar("_LicenseT", bound=License)


class LicenseTestBase(Generic[_LicenseT]):
    """
    A base class for testing :py:class:`betty.license.License` implementations.
    """

    @pytest.fixture
    def sut(self) -> type[_LicenseT]:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    def test_summary(self, sut: _LicenseT) -> None:
        """
        Tests :py:meth:`betty.license.License.summary` implementations.
        """
        assert sut.summary.localize(DEFAULT_LOCALIZER)

    def test_text(self, sut: _LicenseT) -> None:
        """
        Tests :py:meth:`betty.license.License.text` implementations.
        """
        assert sut.text.localize(DEFAULT_LOCALIZER)

    def test_url(self, sut: _LicenseT) -> None:
        """
        Tests :py:meth:`betty.license.License.url` implementations.
        """
        url = sut.url
        if url is not None:
            assert url.localize(DEFAULT_LOCALIZER)
