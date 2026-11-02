from betty.attrs.countable_localizable import new_countable_localizable_attr
from betty.locale import default_locale_tag
from betty.localizables.static import CountableStaticTranslations
from betty.localizer import default_localizer
from betty.prop import HasProps


class _Owner(HasProps):
    attr = new_countable_localizable_attr(label="-")


def test_new_countable_localizable_attr() -> None:
    owner = _Owner()
    translation = CountableStaticTranslations({
        default_locale_tag: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    })
    owner.attr = translation
    assert owner.attr.count(2).localize(default_localizer) == "2 worlds"
