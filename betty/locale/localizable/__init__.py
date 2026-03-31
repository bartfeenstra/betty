"""
The localizable API allows objects to be localized at the point of use.
"""

from __future__ import annotations

import decimal
from abc import ABC, abstractmethod
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, override
from warnings import warn

from babel import Locale

from betty.locale import HasLocale, HasLocaleStr, ResolvableLocale
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer

if TYPE_CHECKING:
    from betty.typing import Intersection


class _Localizable[T](ABC):
    @abstractmethod
    def format(self, **format_kwargs: ResolvableLocalizable) -> T:
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

    @abstractmethod
    def localize(self, localizer: Localizer, /) -> Intersection[HasLocale, str]:
        """
        Localize ``self`` to a human-readable string.
        """

    @override
    def format(self, **format_kwargs: ResolvableLocalizable) -> Localizable:
        return _FormattedLocalizable(self, format_kwargs)

    @override
    def __str__(self) -> str:
        localized = self.localize(DEFAULT_LOCALIZER)
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

    @abstractmethod
    def count(self, count: LocalizableCount, /) -> Localizable:
        """
        Create a localizable for the given count (number of things).

        Implementations MUST automatically format the returned localizable with a ``{count}`` argument set to ``count``.
        """

    @override
    def format(self, **format_kwargs: ResolvableLocalizable) -> CountableLocalizable:
        return _FormattedCountableLocalizable(self, format_kwargs)


class _FormattedLocalizable(Localizable):
    def __init__(
        self,
        localizable: Localizable,
        format_kwargs: Mapping[str, ResolvableLocalizable],
        /,
    ):
        self._localizable = localizable
        self._format_kwargs = dict(format_kwargs)

    @override
    def format(self, **format_kwargs: ResolvableLocalizable) -> Localizable:
        self._format_kwargs.update(format_kwargs)
        return self

    @override
    def localize(self, localizer: Localizer, /) -> Intersection[HasLocale, str]:
        return HasLocaleStr(
            self._localizable.localize(localizer).format(
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
        format_kwargs: Mapping[str, ResolvableLocalizable],
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


type StaticTranslationsMapping = MutableMapping[Locale | None, str]
"""
Static translations for :py:class:`betty.locale.localizable.static.StaticTranslations`.

Values are a string, or a mapping of locales to translations.

See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


type ShorthandStaticTranslations = (
    MutableMapping[ResolvableLocale | None, str] | str | StaticTranslationsMapping
)
"""
Static translations for :py:class:`betty.locale.localizable.static.StaticTranslations`.

Values are a string, or a mapping of locales or language tags to translations.

See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


type CountableStaticTranslationsMapping = MutableMapping[
    Locale, MutableMapping[str, str]
]
"""
Countable static translations for :py:class:`betty.locale.localizable.CountableStaticTranslations`.

Values are mappings of locales to mappings of CLDR plural tags to translations.

See :py:func:`betty.locale.localizable.assertion.assert_countable_static_translations`.
"""


type ShorthandCountableStaticTranslations = MutableMapping[
    ResolvableLocale, MutableMapping[str, str]
]
"""
Static translations for :py:class:`betty.locale.localizable.static.StaticTranslations`.

Values are mappings of locales or language tags to mappings of CLDR plural tags to translations.

See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


type ResolvableLocalizable = Localizable | ShorthandStaticTranslations
"""
A localizable, or a type that can be converted into a localizable with :py:func:`betty.locale.localizable.ensure_localizable`.
"""


type ResolvableCountableLocalizable = (
    CountableLocalizable | ShorthandCountableStaticTranslations
)
"""
A countable localizable, or a type that can be converted into a countable localizable with :py:func:`betty.locale.localizable.ensure_countable_localizable`.
"""


def resolve_localizable(localizable: ResolvableLocalizable) -> Localizable:
    """
    Ensure that a localizable-like value is or is made to be an actual localizable.
    """
    if isinstance(localizable, Localizable):
        return localizable
    if isinstance(localizable, str):
        from betty.locale.localizable.plain import Plain

        return Plain(localizable)
    from betty.locale.localizable.static import StaticTranslations

    return StaticTranslations(localizable)


def resolve_countable_localizable(
    localizable: ResolvableCountableLocalizable,
) -> CountableLocalizable:
    """
    Ensure that a countable-localizable-like value is or is made to be an actual countable localizable.
    """
    if isinstance(localizable, CountableLocalizable):
        return localizable
    from betty.locale.localizable.static import CountableStaticTranslations

    return CountableStaticTranslations(localizable)
