from gettext import NullTranslations

from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.property import (
    CountableLocalizableProperty,
    LocalizableProperty,
)
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestLocalizableProperty:
    class _Instance:
        attr = LocalizableProperty(label=DUMMY_LOCALIZABLE)

    def test___set____with_str(self) -> None:
        instance = self._Instance()
        translation = "Hello, world!"
        instance.attr = translation
        assert instance.attr.localize(DEFAULT_LOCALIZER) == translation

    def test___set____with_mapping(self) -> None:
        instance = self._Instance()
        translation = "Hello, world!"
        locale = "nl-NL"
        instance.attr = {
            DEFAULT_LOCALE_TAG: "Hello, world!",
            locale: translation,
        }
        assert (
            instance.attr.localize(Localizer(locale, NullTranslations())) == translation
        )

    def test___set____with_localizable(self) -> None:
        instance = self._Instance()
        localizable = Plain("Hello, world!")
        instance.attr = localizable
        assert instance.attr is localizable


class TestCountableLocalizableProperty:
    class _Instance:
        attr = CountableLocalizableProperty(label=DUMMY_LOCALIZABLE)

    def test___set____with_shorthand(self) -> None:
        instance = self._Instance()
        translation = {
            DEFAULT_LOCALE_TAG: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
        instance.attr = translation
        assert instance.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"

    def test___set____with_mapping(self) -> None:
        instance = self._Instance()
        translation = {
            DEFAULT_LOCALE: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
        instance.attr = translation
        assert instance.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"
