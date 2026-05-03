"""
Countable localizable properties.
"""

from __future__ import annotations

from typing import final

from betty.locale.localizable import (
    CountableLocalizable,
    ResolvableCountableLocalizable,
    ResolvableLocalizable,
    resolve_countable_localizable,
)
from betty.locale.localizable.data import CountableLocalizableDefinition
from betty.property import Property


@final
class CountableLocalizableProperty(
    Property[CountableLocalizable, ResolvableCountableLocalizable]
):
    """
    A property containing a :py:class:`betty.locale.localizable.CountableLocalizable`.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            CountableLocalizableDefinition(),
            label=label,
            description=description,
            resolver=resolve_countable_localizable,
        )
