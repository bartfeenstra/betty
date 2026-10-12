"""
The localizable API allows objects to be localized at the point of use.
"""

from __future__ import annotations

import decimal
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, override
from warnings import warn

from betty.freezers.attr import AttrFreezable
from betty.localized import LocalizedStr
from betty.localizer import AnyLocalizable, Localizer, default_localizer

if TYPE_CHECKING:
    from collections.abc import Mapping


class _Localizable[T](metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def format(self, **format_kwargs: AnyLocalizable) -> T:
        """
        Apply string formatting to the eventual localized string.

        The arguments are identical to those of :py:meth:`str.format`.

        :return:
            A new localizable object.
        """


class Localizable(_Localizable["Localizable"]):
    """
    A localizable object.

    Objects of this type can convert themselves to localized strings at the point of use.
    """

    __slots__ = ()

    @abstractmethod
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        """
        Localize ``self`` to a human-readable string.
        """

    @override
    def format(self, **format_kwargs: AnyLocalizable) -> Localizable:
        return _FormattedLocalizable(self, format_kwargs)

    @override
    def __str__(self) -> str:
        localized = self.localize(default_localizer)
        warn(
            f'{type(self)} ("{localized}") SHOULD NOT be cast to a string. Instead, call {type(self)}.localize() to ensure it is always formatted in the desired locale.',
            stacklevel=2,
        )
        return localized


type LocalizableCount = int | float | decimal.Decimal
"""
A count to localize strings for.

Based on :py:meth:`babel.plural.PluralRule.__call__`.
"""


class CountableLocalizable(_Localizable["CountableLocalizable"]):
    """
    An object that can be localized for a specific count (number of things).
    """

    __slots__ = ()

    @abstractmethod
    def count(self, count: LocalizableCount, /) -> Localizable:
        """
        Create a localizable for the given count (number of things).

        Implementations MUST automatically format the returned localizable with a ``{count}`` argument set to ``count``.
        """

    @override
    def format(self, **format_kwargs: AnyLocalizable) -> CountableLocalizable:
        return _FormattedCountableLocalizable(self, format_kwargs)


class _FormattedLocalizable(AttrFreezable, Localizable):
    def __init__(
        self,
        localizable: Localizable,
        format_kwargs: Mapping[str, AnyLocalizable],
        /,
    ):
        super().__init__()
        self._localizable = localizable
        self._format_kwargs = dict(format_kwargs)

    @override
    def format(self, **format_kwargs: AnyLocalizable) -> Localizable:
        self._format_kwargs.update(format_kwargs)
        return self

    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        return LocalizedStr(
            localizer.localize(self._localizable).format(
                **{
                    format_kwarg_key: format_kwarg.localize(localizer)
                    if isinstance(format_kwarg, Localizable)
                    else format_kwarg
                    for format_kwarg_key, format_kwarg in self._format_kwargs.items()
                },
            )
        )


class _FormattedCountableLocalizable(CountableLocalizable):
    def __init__(
        self,
        localizable: CountableLocalizable,
        format_kwargs: Mapping[str, AnyLocalizable],
        /,
    ):
        self._localizable = localizable
        self._format_kwargs = format_kwargs

    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return _FormattedLocalizable(
            self._localizable.count(count),
            {**self._format_kwargs, "count": str(count)},
        )
