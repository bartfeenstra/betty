"""
Provide localizable configuration.
"""

from contextlib import suppress
from typing import Self, final

from typing_extensions import override

from betty.assertion import assert_len
from betty.attr import SettableAttr, DeletableAttr
from betty.config import Configuration
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import (
    ShorthandStaticTranslations,
    StaticTranslationsLocalizable,
)
from betty.locale.localizable.assertion import assert_static_translations
from betty.serde.dump import Dump, minimize
from betty.typing import Voidable


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

        translations = assert_static_translations()(dump)
        assert_len(minimum=1 if self._required else 0)(translations)
        for locale, translation in translations.items():
            self[locale] = translation

    @override
    def dump(self) -> Voidable[Dump]:
        if len(self._translations) == 1:
            with suppress(KeyError):
                return self._translations[UNDETERMINED_LOCALE]
        return minimize(self._translations, True)


class _StaticTranslationsLocalizableConfigurationAttr(
    SettableAttr[
        object, StaticTranslationsLocalizableConfiguration, ShorthandStaticTranslations
    ],
):
    _required: bool

    @override
    def new_attr(self, instance: object) -> StaticTranslationsLocalizableConfiguration:
        return StaticTranslationsLocalizableConfiguration(required=self._required)

    @override
    def set_attr(self, instance: object, value: ShorthandStaticTranslations) -> None:
        self.get_attr(instance).replace(value)


@final
class RequiredStaticTranslationsLocalizableConfigurationAttr(
    _StaticTranslationsLocalizableConfigurationAttr
):
    """
    An instance attribute that contains :py:class:`betty.locale.localizable.config.StaticTranslationsLocalizableConfiguration`.
    """

    _required = True


@final
class OptionalStaticTranslationsLocalizableConfigurationAttr(
    _StaticTranslationsLocalizableConfigurationAttr,
    DeletableAttr[
        object, StaticTranslationsLocalizableConfiguration, ShorthandStaticTranslations
    ],
):
    """
    An instance attribute that contains :py:class:`betty.locale.localizable.config.StaticTranslationsLocalizableConfiguration`.
    """

    _required = False

    @override
    def del_attr(self, instance: object) -> None:
        self.get_attr(instance).replace({})
