from betty.attrs.localizable import new_countable_localizable_attr, new_localizable_attr
from betty.classtools.init import Init
from betty.locale import default_locale_tag
from betty.localizables.static import CountableStaticTranslations
from betty.localizer import default_localizer


class _Owner(Init):
    attr = new_localizable_attr(label="-")


def test_new_localizable_attr() -> None:
    owner = _Owner()
    localizable = "Hello, world!"
    owner.attr = localizable
    assert owner.attr == localizable


class _CountableOwner(Init):
    attr = new_countable_localizable_attr(label="-")


def test_new_countable_localizable_attr() -> None:
    owner = _CountableOwner()
    translation = CountableStaticTranslations({
        default_locale_tag: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    })
    owner.attr = translation
    assert owner.attr.count(2).localize(default_localizer) == "2 worlds"
