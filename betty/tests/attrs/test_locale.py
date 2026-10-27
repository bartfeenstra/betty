from __future__ import annotations

from babel import Locale

from betty.attrs.locale import HasLocale, new_locale_attr
from betty.locale import default_locale, default_locale_tag
from betty.prop import HasProps


class _Owner(HasProps):
    locale = new_locale_attr()


def test_new_locale_attr__set() -> None:
    sut = _Owner()
    sut.locale = default_locale_tag
    assert sut.locale == default_locale


class TestHasLocale:
    def test_locale_without___init___locale(self) -> None:
        sut = HasLocale()
        assert sut.locale is None

    def test_locale_with___init___locale(self) -> None:
        locale = Locale("nl")
        sut = HasLocale(locale=locale)
        assert sut.locale is locale

    def test_locale(self) -> None:
        locale = Locale("nl")
        sut = HasLocale()
        sut.locale = locale
        assert sut.locale == locale
