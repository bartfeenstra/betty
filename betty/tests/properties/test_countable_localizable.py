from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.properties.countable_localizable import CountableLocalizableProperty
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


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
        instance.attr = translation  # ty:ignore[invalid-assignment]
        assert instance.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"

    def test___set____with_mapping(self) -> None:
        instance = self._Instance()
        translation = {
            DEFAULT_LOCALE: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
        instance.attr = translation  # ty:ignore[invalid-assignment]
        assert instance.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"
