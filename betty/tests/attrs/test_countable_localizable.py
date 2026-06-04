from betty.attrs.countable_localizable import new_countable_localizable_attr
from betty.locale import default_locale, default_locale_tag
from betty.locale.localize import default_localizer
from betty.prop import HasProps


class _Owner(HasProps):
    attr = new_countable_localizable_attr(label="-")


def test_new_countable_localizable_attr____set___with_shorthand() -> None:
    owner = _Owner()
    translation = {
        default_locale_tag: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    }
    owner.attr = translation  # ty:ignore[invalid-assignment]
    assert owner.attr.count(2).localize(default_localizer) == "2 worlds"


def test_new_countable_localizable_attr____set___with_mapping() -> None:
    owner = _Owner()
    translation = {
        default_locale: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    }
    owner.attr = translation  # ty:ignore[invalid-assignment]
    assert owner.attr.count(2).localize(default_localizer) == "2 worlds"
