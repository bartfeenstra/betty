"""
Pytest configuration.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum
from inspect import signature
from typing import Any, Final, final
from unittest.mock import Mock
from warnings import filterwarnings

import aiohttp
import pytest

from betty.test_utils.conftest import *  # noqa: F403
from betty.warnings import BettyDeprecationWarning

type Markable = Callable[..., object] | type


@final
class Duration(IntEnum):
    MINUTES = 1
    SECONDS = 499999999
    NEGLIGIBLE = 999999999
    DEFAULT = NEGLIGIBLE


default_timeout: Final[int] = 9


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        item_duration = min((
            Duration.DEFAULT,
            *(marker.args[0] for marker in item.iter_markers("duration")),
        ))
        item_timeout = max((
            default_timeout,
            *(marker.args[0] for marker in item.iter_markers("timeout")),
        ))

        # For tests setting a duration marker directly, reflect this in the item's timeout
        match item_duration:
            case Duration.MINUTES:
                item_timeout = max(item_timeout, 300)
            case Duration.SECONDS:
                item_timeout = max(item_timeout, 60)

        # Each order marker creates a parameterized test matrix, which we do not want to do here, so only set an order
        # marker if none existed yet.
        if not item.get_closest_marker("order"):
            item.add_marker(pytest.mark.order(item_duration.value))
        # pytest-timeout works based on the closest found marker, so we prepend ours to make that happen.
        item.add_marker(pytest.mark.timeout(item_timeout), False)


@pytest.fixture(autouse=True)
def _raise_deprecation_warnings_as_errors() -> None:
    """
    Raise Betty's own deprecation warnings as errors.
    """
    filterwarnings(
        "error",
        category=BettyDeprecationWarning,
    )


def playwright_test[MarkableT: Markable](markable: MarkableT, /) -> MarkableT:
    """
    Mark a test item to require Playwright.
    """
    markable = pytest.mark.playwright(markable)
    markable = pytest.mark.asyncio(loop_scope="session")(markable)
    return pytest.mark.duration(Duration.SECONDS)(markable)


def webpack_test[MarkableT: Markable](markable: MarkableT, /) -> MarkableT:
    """
    Mark a test item to require Webpack.
    """
    markable = pytest.mark.webpack(markable)
    return pytest.mark.duration(Duration.MINUTES)(markable)


# Work around a problem where aiohttp 3.14 added a required kwarg ``stream_writer``, which aioresponses does not yet
# support.
_aiohttp_client_response_init = aiohttp.ClientResponse.__init__
if "stream_writer" in signature(_aiohttp_client_response_init).parameters:

    def _init(*args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("stream_writer", Mock(output_size=0))
        _aiohttp_client_response_init(*args, **kwargs)

    aiohttp.ClientResponse.__init__ = _init
