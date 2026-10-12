"""
Reusable validators that implement the :py:mod:`validation API <betty.validation>`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.classtools import abstract
from betty.localizer import default_localizer
from betty.validation import StaticInvalid

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.location import ResolvableLocation


@abstract
class InvalidValue[ValueT](StaticInvalid[ValueT], ValueError):
    """
    A helper to create :py:class:`betty.validation.Invalid` subclasses that are also :py:class:`ValueError`.
    """

    def __init__(
        self,
        value: ValueT,
        message: ResolvableLocalizable | None = None,
        /,
        *,
        hint: ResolvableLocalizable | None = None,
        at: ResolvableLocation = (),
        url: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            value,
            default_localizer.localize(self._message if message is None else message),
            hint=hint,
            at=at,
            message=message,
            url=url,
        )
