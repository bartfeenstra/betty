from gettext import NullTranslations

import pytest

from betty.attr import AttrNotInitialized
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable.attr import (
    OptionalLocalizableAttr,
    RequiredCountableLocalizableAttr,
    RequiredLocalizableAttr,
)
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer


class TestRequiredLocalizableAttr:
    class _Instance:
        attr = RequiredLocalizableAttr("attr")

    def test___get____not_initialized(self) -> None:
        instance = self._Instance()
        with pytest.raises(AttrNotInitialized):
            instance.attr  # noqa: B018

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


class TestOptionalLocalizableAttr:
    class _Instance:
        attr = OptionalLocalizableAttr("attr")

    def test___get____not_initialized(self) -> None:
        instance = self._Instance()
        assert instance.attr is None

    def test___set____with_str(self) -> None:
        translation = "Hello, world!"
        instance = self._Instance()
        instance.attr = translation
        assert instance.attr is not None
        assert instance.attr.localize(DEFAULT_LOCALIZER) == translation

    def test___set____with_mapping(self) -> None:
        instance = self._Instance()
        translation = "Hello, world!"
        locale = "nl-NL"
        instance.attr = {
            DEFAULT_LOCALE_TAG: "Hello, world!",
            locale: translation,
        }
        assert instance.attr is not None
        assert (
            instance.attr.localize(Localizer(locale, NullTranslations())) == translation
        )

    def test___set____with_localizable(self) -> None:
        instance = self._Instance()
        localizable = Plain("Hello, world!")
        instance.attr = localizable
        assert instance.attr is localizable

    def test___delete____without_value(self) -> None:
        instance = self._Instance()
        del instance.attr
        assert instance.attr is None

    def test___delete____with_value(self) -> None:
        instance = self._Instance()
        instance.attr = "Hello, world!"
        del instance.attr
        assert instance.attr is None


class TestRequiredCountableLocalizableAttr:
    class _Instance:
        attr = RequiredCountableLocalizableAttr("attr")

    def test___get____not_initialized(self) -> None:
        instance = self._Instance()
        with pytest.raises(AttrNotInitialized):
            instance.attr  # noqa: B018

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
