"""
Provide localizable configuration.
"""

from contextlib import suppress
from typing import Self, final

from typing_extensions import override

from betty.attr import MutableAttr
from betty.config import Configuration
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import (
    ShorthandStaticTranslations,
    StaticTranslationsLocalizable,
)
from betty.serde.dump import VoidableDump, Dump, minimize
from betty.typing import Void


@final
class StaticTranslationsLocalizableConfiguration(
    Configuration, StaticTranslationsLocalizable
):
    """
    Provide configuration for a :py:class:`betty.locale.localizable.Localizable`.

    Read more at :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
    """

    @override
    def update(self, other: Self) -> None:
        self._translations = other._translations

    @override
    def load(self, dump: Dump) -> None:
        self._translations.clear()
        for locale, translation in self._assert_shorthand_translations(dump).items():
            self[locale] = translation

    @override
    def dump(self) -> VoidableDump:
        if not len(self._translations):
            return Void
        if len(self._translations) == 1:
            with suppress(KeyError):
                return self._translations[UNDETERMINED_LOCALE]
        return minimize(
            self._translations  # type: ignore[arg-type]
        )


@final
class StaticTranslationsLocalizableConfigurationAttr(
    MutableAttr[
        object, StaticTranslationsLocalizableConfiguration, ShorthandStaticTranslations
    ],
):
    """
    An instance attribute that contains :py:class:`betty.locale.localizable.config.StaticTranslationsLocalizableConfiguration`.
    """

    def __init__(self, attr_name: str, *, required: bool = True):
        super().__init__(attr_name)
        self._required = required

    @override
    def new_attr(self, instance: object) -> StaticTranslationsLocalizableConfiguration:
        return StaticTranslationsLocalizableConfiguration(required=self._required)

    @override
    def set_attr(self, instance: object, value: ShorthandStaticTranslations) -> None:
        self.get_attr(instance).replace(value)

    @override
    def del_attr(self, instance: object) -> None:
        self.get_attr(instance).replace({})
