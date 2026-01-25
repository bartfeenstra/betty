from gettext import NullTranslations

from betty.app import App
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.property import (
    CountableLocalizableProperty,
    LocalizableProperty,
)
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.project import Project
from betty.test_utils.json.linked_data import assert_linked_data_dump
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

    async def test_dump_linked_data(self) -> None:
        instance = self._Instance()
        localizable = Plain("Hello, world!")
        instance.attr = localizable

        actual = await assert_linked_data_dump(
            StaticTranslationsSchema(),
            lambda project: self._Instance.attr.dump_linked_data(project, instance),
        )
        assert actual == {"en-US": "Hello, world!"}

    async def test_linked_data_schema(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._Instance.attr.linked_data_schema(project)


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
