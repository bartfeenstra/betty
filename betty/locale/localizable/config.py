"""
Provide localizable configuration.
"""

from contextlib import suppress
from typing import Self, TypeVar, cast, final, overload

from typing_extensions import override

from betty.assertion import assert_len
from betty.config import Configuration
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import (
    ShorthandStaticTranslations,
    StaticTranslations,
)
from betty.locale.localizable.assertion import assert_static_translations
from betty.serde.dump import Dump

_T = TypeVar("_T")


@final
class StaticTranslationsConfiguration(Configuration, StaticTranslations):
    """
    Provide configuration for a :py:class:`betty.locale.localizable.Localizable`.

    Read more at :doc:`multiple translations </usage/configuration/static-translations-localizable>`.
    """

    @override
    def load(self, dump: Dump) -> None:
        self._translations.clear()

        translations = assert_static_translations()(dump)
        assert_len(minimum=1 if self._required else 0)(translations)
        for locale, translation in translations.items():
            self[locale] = translation

    @override
    def dump(self) -> Dump:
        translation_count = len(self._translations)
        if translation_count == 0:
            return {}
        if translation_count == 1:
            with suppress(KeyError):
                return self._translations[UNDETERMINED_LOCALE]
        return dict(self._translations)


class _StaticTranslationsConfigurationAttr:
    _required: bool

    def __init__(self, attr_name: str):
        self._attr_name = f"_{attr_name}"

    @overload
    def __get__(self, instance: None, owner: type[object]) -> Self:
        pass

    @overload
    def __get__(self, instance: _T, owner: type[_T]) -> StaticTranslationsConfiguration:
        pass

    def __get__(
        self, instance: object | None, owner: type[object]
    ) -> StaticTranslationsConfiguration | Self:
        if instance is None:
            return self  # type: ignore[return-value]
        try:
            return cast(
                "StaticTranslationsConfiguration",
                getattr(instance, self._attr_name),
            )
        except AttributeError:
            value = StaticTranslationsConfiguration(required=self._required)
            setattr(instance, self._attr_name, value)
            return value

    def __set__(self, instance: object, value: ShorthandStaticTranslations) -> None:
        self.__get__(instance, type(instance)).replace(value)


@final
class RequiredStaticTranslationsConfigurationAttr(_StaticTranslationsConfigurationAttr):
    """
    An instance attribute that contains :py:class:`betty.locale.localizable.config.StaticTranslationsConfiguration`.
    """

    _required = True


@final
class OptionalStaticTranslationsConfigurationAttr(_StaticTranslationsConfigurationAttr):
    """
    An instance attribute that contains :py:class:`betty.locale.localizable.config.StaticTranslationsConfiguration`.
    """

    _required = False

    def __delete__(self, instance: object) -> None:
        self.__get__(instance, type(instance)).replace({})
