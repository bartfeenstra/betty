from betty.attrs.countable_localizable import CountableLocalizableAttr
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.property import HasProperties


class TestCountableLocalizableAttr:
    class _Owner(HasProperties):
        attr = CountableLocalizableAttr(label="-")

    def test___set____with_shorthand(self) -> None:
        owner = self._Owner()
        translation = {
            DEFAULT_LOCALE_TAG: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
        owner.attr = translation  # ty:ignore[invalid-assignment]
        assert owner.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"

    def test___set____with_mapping(self) -> None:
        owner = self._Owner()
        translation = {
            DEFAULT_LOCALE: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
        owner.attr = translation  # ty:ignore[invalid-assignment]
        assert owner.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"
