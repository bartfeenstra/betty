"""
Reusable validators that implement the :py:mod:`validation API <betty.validation>`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.validation import Invalid

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.localizable import ResolvableLocalizable
    from betty.user.location import Locator


class _StaticMessageInvalid(Invalid):
    _message: ResolvableLocalizable

    def __init__(
        self,
        value: Any,
        /,
        *,
        location: Iterable[Locator] = (),
    ):
        super().__init__(value, self._message)
