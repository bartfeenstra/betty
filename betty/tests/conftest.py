"""
Pytest configuration.
"""

from __future__ import annotations

from os import environ
from warnings import filterwarnings

import pytest

from betty.test_utils.conftest import *  # noqa: F403
from betty.warnings import BettyDeprecationWarning


@pytest.fixture(autouse=True)
def _raise_deprecation_warnings_as_errors() -> None:
    """
    Raise Betty's own deprecation warnings as errors.
    """
    filterwarnings(
        "error",
        category=BettyDeprecationWarning,
    )


check_skip_playwright = pytest.mark.skipif(
    environ.get("BETTY_TEST_SKIP_PLAYWRIGHT", False) is not False,
    reason="Playwright tests are being skipped",
)
