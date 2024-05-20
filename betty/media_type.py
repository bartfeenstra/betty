"""
Provide `media type <https://en.wikipedia.org/wiki/Media_type>`_ handling utilities.
"""

from __future__ import annotations

from email.message import EmailMessage
from typing import Any

from typing_extensions import override


class InvalidMediaType(ValueError):
    """
    Raised when an identifier is not a valid media type.
    """

    pass  # pragma: no cover


class MediaType:
    """
    Define a `media type <https://en.wikipedia.org/wiki/Media_type>`_.

    Media types are also commonly known as content types or MIME types.
    """

    def __init__(self, media_type: str):
        self._str = media_type
        message = EmailMessage()
        message["Content-Type"] = media_type
        type_part = message.get_content_type()
        # EmailMessage.get_content_type() always returns a type, and will fall back to alternatives if the header is
        # invalid.
        if not media_type.startswith(type_part):
            raise InvalidMediaType(f'"{media_type}" is not a valid media type.')
        self._parameters: dict[str, str] = dict(message["Content-Type"].params)
        self._type, self._subtype = type_part.split("/")
        if not self._subtype:
            raise InvalidMediaType("The subtype must not be empty.")

    def __hash__(self) -> int:
        return hash(self._str)

    @property
    def type(self) -> str:
        """
        The suffix, e.g. ``application`` for ``application/ld+json``.
        """
        return self._type

    @property
    def subtype(self) -> str:
        """
        The subtype, e.g. ``"vnd.oasis.opendocument.text"`` for ``"application/vnd.oasis.opendocument.text"``.
        """
        return self._subtype

    @property
    def subtypes(self) -> list[str]:
        """
        The subtype parts, e.g. ``["vnd", "oasis", "opendocument", "text"]`` for ``"application/vnd.oasis.opendocument.text"``.
        """
        return self._subtype.split("+")[0].split(".")

    @property
    def suffix(self) -> str | None:
        """
        The suffix, e.g. ``+json`` for ``application/ld+json``.
        """
        if "+" not in self._subtype:
            return None

        return self._subtype.split("+")[-1]

    @property
    def parameters(self) -> dict[str, str]:
        """
        The parameters, e.g. ``{"charset": "UTF-8"}`` for ``"text/html; charset=UTF-8"``.
        """
        return self._parameters

    @override
    def __str__(self) -> str:
        return self._str

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MediaType):
            return NotImplemented
        return (self.type, self.subtype, self.parameters) == (
            other.type,
            other.subtype,
            other.parameters,
        )
