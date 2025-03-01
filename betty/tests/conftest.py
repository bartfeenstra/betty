"""
Pytest configuration.
"""

from __future__ import annotations

import multiprocessing
from os import environ
from warnings import filterwarnings

import pytest

from betty.test_utils.conftest import *  # noqa F403
from betty.warnings import BettyDeprecationWarning
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _raise_deprecation_warnings_as_errors() -> None:
    """
    Raise Betty's own deprecation warnings as errors.
    """
    filterwarnings(
        "error",
        category=BettyDeprecationWarning,
    )


@pytest.fixture(scope="session")
def multiprocessing_manager() -> Iterator[SyncManager]:
    """
    Raise Betty's own deprecation warnings as errors.
    """
    with multiprocessing.Manager() as manager:
        yield manager


check_skip_playwright = pytest.mark.skipif(
    environ.get("BETTY_TEST_SKIP_PLAYWRIGHT", False) is not False,
    reason="Playwright tests are being skipped",
)
