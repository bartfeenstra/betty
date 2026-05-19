from gettext import NullTranslations

from betty.attrs.localizable import new_localizable_attr
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.property import HasProperties


class _Owner(HasProperties):
    attr = new_localizable_attr(label="-")


def test_new_localizable_attr____set___with_str() -> None:
    owner = _Owner()
    translation = "Hello, world!"
    owner.attr = translation
    assert owner.attr.localize(DEFAULT_LOCALIZER) == translation


def test_new_localizable_attr____set___with_mapping() -> None:
    owner = _Owner()
    translation = "Hello, world!"
    locale = "nl-NL"
    owner.attr = {  # ty:ignore[invalid-assignment]
        DEFAULT_LOCALE_TAG: "Hello, world!",
        locale: translation,
    }
    assert owner.attr.localize(Localizer(locale, NullTranslations())) == translation


def test_new_localizable_attr____set___with_localizable() -> None:
    owner = _Owner()
    localizable = Plain("Hello, world!")
    owner.attr = localizable
    assert owner.attr is localizable
