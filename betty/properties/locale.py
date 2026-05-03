"""
Locale properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.datas.locale import LocaleDefinition
from betty.locale import resolve_locale
from betty.property import Property

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


@final
class LocaleProperty(Property):
    """
    A property containing a locale.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            LocaleDefinition(),
            label=label,
            description=description,
            resolver=resolve_locale,
        )
