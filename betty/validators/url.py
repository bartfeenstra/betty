"""
URL validators.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, final, overload, override
from urllib.parse import urlsplit, urlunsplit

from betty.localizables.gettext import _
from betty.pipeline import Inlet, Pipeline
from betty.validators import InvalidValue
from betty.validators.int import is_int
from betty.validators.none import is_optional
from betty.validators.str import is_str

if TYPE_CHECKING:
    from betty.validation import Validator


@final
class NotAUrl(InvalidValue):
    """
    Raised when a value is not a valid URL.
    """

    _message = _("This is not a valid URL.")


_is_port = is_optional(is_int(min=0, max=65535))


@final
class _IsUrl(Pipeline[Any, str]):
    @overload
    def __call__(
        self,
        value: Any,
        /,
        *,
        scheme: Validator[str, str] | None = None,
        hostname: Validator[str | None, str | None] | None = None,
        port: Validator[int | None, int | None] | None = None,
        path: Validator[str, str] | None = None,
        query: Validator[str, str] | None = None,
    ) -> str:
        pass

    @overload
    def __call__(
        self,
        *,
        scheme: Validator[str, str] | None = None,
        hostname: Validator[str | None, str | None] | None = None,
        port: Validator[int | None, int | None] | None = None,
        path: Validator[str, str] | None = None,
        query: Validator[str, str] | None = None,
    ) -> Pipeline[Any, str]:
        pass

    @override
    def __call__(
        self, *value_, scheme=None, hostname=None, port=None, path=None, query=None
    ):
        if value_:
            value = is_str(*value_)
            try:
                url_parts = urlsplit(value)
            except ValueError:
                raise NotAUrl(value) from None
            is_port = _is_port
            if port:
                is_port |= port
            validated_netloc = (
                hostname(url_parts.hostname) if hostname else url_parts.hostname
            ) or ""
            validated_port = is_port(url_parts.port)
            if validated_port is not None:
                validated_netloc += ":" + str(validated_port)
            if url_parts.username is not None:
                validated_netloc = "@" + validated_netloc
                if url_parts.password is not None:
                    validated_netloc = ":" + url_parts.password + validated_netloc
                validated_netloc = url_parts.username + validated_netloc
            return urlunsplit(
                url_parts._replace(
                    scheme=scheme(url_parts.scheme) if scheme else url_parts.scheme,
                    netloc=validated_netloc,
                    path=path(url_parts.path) if path else url_parts.path,
                    query=query(url_parts.query) if query else url_parts.query,
                    fragment=url_parts.fragment,
                )
            )
        return Inlet(
            partial(self, scheme=scheme, hostname=hostname, port=port, query=query)
        )


is_url = _IsUrl()
"""
Validate that a value is a valid URL.
"""
