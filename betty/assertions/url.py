"""
URL assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit

from betty.assertions import _HumanFacingValueError
from betty.assertions.str import assert_str
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.functools import Pipeline


def assert_url() -> Pipeline[Any, str]:
    """
    Assert that a value is a valid URL.
    """

    def _assert_url(value: str) -> str:
        try:
            url_parts = urlsplit(value)
        except ValueError:
            raise _HumanFacingValueError(
                _('"{url}" is not a valid URL.').format(url=value)
            ) from None
        if not url_parts.netloc:
            raise _HumanFacingValueError(_("The URL must include a host."))
        if not url_parts.scheme:
            url_parts = url_parts._replace(scheme="https")
        return urlunsplit(url_parts)

    return assert_str() | _assert_url
