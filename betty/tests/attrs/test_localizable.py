from gettext import NullTranslations

from betty.attrs.localizable import LocalizableAttr
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.property import HasProperties
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestLocalizableAttr:
    class _Owner(HasProperties):
        attr = LocalizableAttr(label=DUMMY_LOCALIZABLE)

    def test___set____with_str(self) -> None:
        owner = self._Owner()
        translation = "Hello, world!"
        owner.attr = translation
        assert owner.attr.localize(DEFAULT_LOCALIZER) == translation

    def test___set____with_mapping(self) -> None:
        owner = self._Owner()
        translation = "Hello, world!"
        locale = "nl-NL"
        owner.attr = {  # ty:ignore[invalid-assignment]
            DEFAULT_LOCALE_TAG: "Hello, world!",
            locale: translation,
        }
        assert owner.attr.localize(Localizer(locale, NullTranslations())) == translation

    def test___set____with_localizable(self) -> None:
        owner = self._Owner()
        localizable = Plain("Hello, world!")
        owner.attr = localizable
        assert owner.attr is localizable
