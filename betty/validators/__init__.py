"""
Reusable validators that implement the :py:mod:`validation API <betty.validation>`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.validation import Invalid

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.location import ResolvableLocation


class _StaticInvalid(Invalid):
    _message: ResolvableLocalizable
    _hint: ResolvableLocalizable | None = None
    _url: ResolvableLocalizable | None = None

    def __init__(
        self,
        value: Any,
        /,
        *args: Any,
        hint: ResolvableLocalizable | None = None,
        location: ResolvableLocation = (),
        message: ResolvableLocalizable | None = None,
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            value,
            hint=self._hint if hint is None else hint,
            location=location,
            message=self._message if message is None else message,
            url=self._url if url is None else url,
        )
