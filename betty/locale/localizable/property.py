"""
Localizable attributes.
"""

from __future__ import annotations

from typing import TypeVar, final

from betty.data.aggregate.record.object.property import Property
from betty.locale.localizable import (
    CountableLocalizable,
    Localizable,
    ResolvableCountableLocalizable,
    ResolvableLocalizable,
    resolve_countable_localizable,
    resolve_localizable,
)
from betty.locale.localizable.data import (
    CountableLocalizableDefinition,
    LocalizableDefinition,
)

_ValueGetT = TypeVar("_ValueGetT")
_ValueSetT = TypeVar("_ValueSetT")


@final
class LocalizableProperty(Property[Localizable, ResolvableLocalizable]):
    """
    A property containing a :py:class:`betty.locale.localizable.Localizable`.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            LocalizableDefinition(),
            label=label,
            description=description,
            resolver=resolve_localizable,
        )


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
