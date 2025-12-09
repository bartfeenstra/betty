"""
Localizable attributes.
"""

from __future__ import annotations

from typing import final

from betty.attr import OptionalAttr, RequiredAttr
from betty.locale.localizable import (
    CountableLocalizable,
    CountableLocalizableLike,
    Localizable,
    LocalizableLike,
)
from betty.locale.localizable.ensure import (
    ensure_countable_localizable,
    ensure_localizable,
)


@final
class RequiredLocalizableAttr(RequiredAttr[Localizable]):
    """
    An attribute for a required :py:class:`betty.locale.localizable.Localizable`.
    """

    def __set__(self, instance: object, value: LocalizableLike, /) -> None:
        setattr(instance, self._attr_name, ensure_localizable(value))


@final
class OptionalLocalizableAttr(OptionalAttr[Localizable | None]):
    """
    An attribute for an optional :py:class:`betty.locale.localizable.Localizable`.
    """

    def __set__(self, instance: object, value: LocalizableLike | None, /) -> None:
        setattr(
            instance,
            self._attr_name,
            None if value is None else ensure_localizable(value),
        )

    def __delete__(self, instance: object) -> None:
        setattr(instance, self._attr_name, None)


@final
class RequiredCountableLocalizableAttr(RequiredAttr[CountableLocalizable]):
    """
    An attribute for a required :py:class:`betty.locale.localizable.CountableLocalizable`.
    """

    def __set__(
        self, instance: object, value: CountableLocalizableLike | None, /
    ) -> None:
        setattr(
            instance,
            self._attr_name,
            None if value is None else ensure_countable_localizable(value),
        )
