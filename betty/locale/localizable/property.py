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
    LocalizableLike,
)
from betty.locale.localizable.data import (
    CountableLocalizableDefinition,
    LocalizableDefinition,
)
from betty.locale.localizable.ensure import (
    ensure_countable_localizable,
    ensure_localizable,
)

_ValueGetT = TypeVar("_ValueGetT")
_ValueSetT = TypeVar("_ValueSetT")


@final
class LocalizableProperty(Property[Localizable, LocalizableLike]):
    """
    A property containing a :py:class:`betty.locale.localizable.Localizable`.
    """

    def __init__(
        self,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        super().__init__(
            LocalizableDefinition(),
            label=label,
            description=description,
            resolver=ensure_localizable,
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
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        super().__init__(
            CountableLocalizableDefinition(),
            label=label,
            description=description,
            resolver=ensure_countable_localizable,
        )
