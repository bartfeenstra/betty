from betty.attrs.countable_localizable import new_countable_localizable_attr
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.property import HasProperties


class _Owner(HasProperties):
    attr = new_countable_localizable_attr(label="-")


def test_new_countable_localizable_attr____set___with_shorthand() -> None:
    owner = _Owner()
    translation = {
        DEFAULT_LOCALE_TAG: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    }
    owner.attr = translation  # ty:ignore[invalid-assignment]
    assert owner.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"


def test_new_countable_localizable_attr____set___with_mapping() -> None:
    owner = _Owner()
    translation = {
        DEFAULT_LOCALE: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    }
    owner.attr = translation  # ty:ignore[invalid-assignment]
    assert owner.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"
