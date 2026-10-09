"""
URL validators.
"""

from __future__ import annotations

from typing import final
from urllib.parse import urlsplit, urlunsplit

from betty.localizables.gettext import _
from betty.validators import _StaticInvalid
from betty.validators.str import is_str


@final
class NotAUrl(_StaticInvalid):
    """
    Raised when a value is not a valid URL.
    """

    _message = _("This is not a valid URL.")


@final
class MissingHost(_StaticInvalid):
    """
    Raised when a URL does not include a host.
    """

    _message = _("The URL must include a host.")


def _is_url(value: str, /) -> str:
    try:
        url_parts = urlsplit(value)
    except ValueError:
        raise NotAUrl(value) from None
    if not url_parts.netloc:
        raise MissingHost(value)
    if not url_parts.scheme:
        url_parts = url_parts._replace(scheme="https")
    return urlunsplit(url_parts)


is_url = is_str | _is_url
"""
Validate that a value is a valid URL.
"""
