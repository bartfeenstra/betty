"""
URL validators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit

from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.validation import Invalid, group
from betty.validators.str import is_str

if TYPE_CHECKING:
    from betty.functools import Pipeline


def is_url() -> Pipeline[Any, str]:
    """
    Validate that a value is a valid URL.
    """

    @group()
    def _is_url(value: str) -> str:
        try:
            url_parts = urlsplit(value)
        except ValueError:
            raise Invalid(
                _("{url} is not a valid URL.").format(url=Quote(value))
            ) from None
        if not url_parts.netloc:
            raise Invalid(_("The URL must include a host."))
        if not url_parts.scheme:
            url_parts = url_parts._replace(scheme="https")
        return urlunsplit(url_parts)

    return is_str | _is_url
