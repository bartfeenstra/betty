"""
Provide localizable configuration.
"""

from contextlib import suppress
from typing import Self, cast, overload, final

from betty.assertion import assert_len_min
from betty.locale.localizable import (
    ShorthandStaticTranslations,
    Localizable,
    StaticTranslationsLocalizable,
)
from betty.locale.localizable.assertion import assert_static_translations
from betty.locale.localizer import Localizer
from typing_extensions import override

from betty.config import Configuration
from betty.locale import UNDETERMINED_LOCALE
from betty.serde.dump import VoidableDump, Dump, minimize
from betty.typing import Void


@final
class StaticTranslationsLocalizableConfiguration(Configuration, Localizable):
    """
    Provide configuration for a :py:class:`betty.locale.localizable.Localizable`.

    Read more at :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
    """

    _translations: dict[str, str]

    def __init__(
        self,
        translations: ShorthandStaticTranslations | None = None,
        *,
        minimum: int = 1,
    ):
        """
        :param translations: Keys are locales, values are translations.
        """
        super().__init__()
        self._minimum = minimum
        self._translations: dict[str, str]
        if translations is not None:
            self.set(translations)
        else:
            self._translations = {}

    def __getitem__(self, locale: str) -> str:
        return self._translations[locale]

    def __setitem__(self, locale: str, translation: str) -> None:
        self._translations[locale] = translation

    def __len__(self) -> int:
        return len(self._translations)

    def set(self, translations: ShorthandStaticTranslations) -> None:
        """
        Set the translations.
        """
        translations = assert_static_translations()(translations)
        assert_len_min(self._minimum)(translations)
        self._translations = dict(translations)

    @override
    def localize(self, localizer: Localizer) -> str:
        if self._translations:
            return StaticTranslationsLocalizable(self._translations).localize(localizer)
        return ""

    @override
    def update(self, other: Self) -> None:
        self._translations = other._translations

    @override
    def load(self, dump: Dump) -> None:
        self._translations.clear()

        translations = assert_static_translations()(dump)
        assert_len_min(self._minimum)(translations)
        for locale, translation in translations.items():
            self[locale] = translation

    @override
    def dump(self) -> VoidableDump:
        if not len(self._translations):
            return Void
        if len(self._translations) == 1:
            with suppress(KeyError):
                return self._translations[UNDETERMINED_LOCALE]
        return minimize(
            self._translations.copy()  # type: ignore[arg-type]
        )


@final
class StaticTranslationsLocalizableConfigurationProperty:
    """
    A property (similar to :py:func:`property`) that contains :py:class:`betty.locale.localizable.Localizable.StaticTranslationsLocalizableConfiguration`.
    """

    def __init__(self, attr_name: str, *, minimum: int = 1):
        self._attr_name = f"_{attr_name}"
        self._minimum = minimum

    def _get(self, instance: object) -> StaticTranslationsLocalizableConfiguration:
        try:
            return cast(
                StaticTranslationsLocalizableConfiguration,
                getattr(instance, self._attr_name),
            )
        except AttributeError:
            translations = StaticTranslationsLocalizableConfiguration(
                minimum=self._minimum
            )
            setattr(instance, self._attr_name, translations)
            return translations

    @overload
    def __get__(self, instance: None, _: type) -> Self:
        pass

    @overload
    def __get__(
        self, instance: object, _: type
    ) -> StaticTranslationsLocalizableConfiguration:
        pass

    def __get__(self, instance, _):
        if instance is None:
            return self
        return self._get(instance)

    def __set__(
        self, instance: object, translations: ShorthandStaticTranslations
    ) -> None:
        self._get(instance).set(translations)

    def __delete__(self, instance: object) -> None:
        self._get(instance).set({})
