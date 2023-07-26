from __future__ import annotations

from email.message import EmailMessage
from typing import Any


class InvalidMediaType(ValueError):
    pass


class MediaType:
    def __init__(self, media_type: str):
        self._str = media_type
        message = EmailMessage()
        message['Content-Type'] = media_type
        type_part = message.get_content_type()
        # EmailMessage.get_content_type() always returns a type, and will fall back to alternatives if the header is
        # invalid.
        if not media_type.startswith(type_part):
            raise InvalidMediaType(f'"{media_type}" is not a valid media type.')
        self._parameters: dict[str, str] = message['Content-Type'].params
        self._type, self._subtype = type_part.split('/')
        if not self._subtype:
            raise InvalidMediaType('The subtype must not be empty.')

    @property
    def type(self) -> str:
        return self._type

    @property
    def subtype(self) -> str:
        return self._subtype

    @property
    def subtypes(self) -> list[str]:
        return self._subtype.split('+')[0].split('.')

    @property
    def suffix(self) -> str | None:
        if '+' not in self._subtype:
            return None

        return self._subtype.split('+')[-1]

    @property
    def parameters(self) -> dict[str, str]:
        return self._parameters

    def __str__(self) -> str:
        return self._str

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MediaType):
            return NotImplemented
        return (self.type, self.subtype, self.parameters) == (other.type, other.subtype, other.parameters)
