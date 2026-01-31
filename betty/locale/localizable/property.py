"""
Localizable attributes.
"""

from __future__ import annotations

from typing import TypeVar, final

from betty.data.aggregate.record.object.property import Property
from betty.locale.localizable import (
    CountableLocalizable,
    CountableLocalizableLike,
    Localizable,
    ResolvableLocalizable,
)
from betty.locale.localizable.data import (
    CountableLocalizableDefinition,
    LocalizableDefinition,
)
from betty.locale.localizable.resolve import (
    resolve_countable_localizable,
    resolve_localizable,
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
    Property[CountableLocalizable, CountableLocalizableLike]
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
