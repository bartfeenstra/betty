"""
Pytest configuration.
"""

from __future__ import annotations

from inspect import signature
from os import environ
from typing import Any
from unittest.mock import Mock
from warnings import filterwarnings

import aiohttp
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
    bool(environ.get("BETTY_TEST_SKIP_PLAYWRIGHT", "")),
    reason="Playwright tests are being skipped",
)

check_skip_webpack_entry_point_provider = pytest.mark.skipif(
    bool(environ.get("BETTY_TEST_SKIP_WEBPACK_ENTRY_POINT_PROVIDER", "")),
    reason="Webpack entry point provider tests are being skipped",
)


# Work around a problem where aiohttp 3.14 added a required kwarg ``stream_writer``, which aioresponses does not yet
# support.
_aiohttp_client_response_init = aiohttp.ClientResponse.__init__
if "stream_writer" in signature(_aiohttp_client_response_init).parameters:

    def _init(*args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("stream_writer", Mock(output_size=0))
        _aiohttp_client_response_init(*args, **kwargs)

    aiohttp.ClientResponse.__init__ = _init
