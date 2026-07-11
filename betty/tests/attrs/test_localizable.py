from gettext import NullTranslations

from betty.attr import Object
from betty.attrs.localizable import new_localizable_attr
from betty.locale import default_locale_tag
from betty.localizables.plain import Plain
from betty.localizer import Localizer, default_localizer


class _Owner(Object):
    attr = new_localizable_attr(label="-")


def test_new_localizable_attr____set___with_str() -> None:
    owner = _Owner()
    translation = "Hello, world!"
    owner.attr = translation
    assert owner.attr.localize(default_localizer) == translation


def test_new_localizable_attr____set___with_mapping() -> None:
    owner = _Owner()
    translation = "Hello, world!"
    locale = "nl-NL"
    owner.attr = {  # ty:ignore[invalid-assignment]
        default_locale_tag: "Hello, world!",
        locale: translation,
    }
    assert owner.attr.localize(Localizer(locale, NullTranslations())) == translation


def test_new_localizable_attr____set___with_localizable() -> None:
    owner = _Owner()
    localizable = Plain("Hello, world!")
    owner.attr = localizable
    assert owner.attr is localizable
