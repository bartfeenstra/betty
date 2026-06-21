from __future__ import annotations

from babel import Locale

from betty.localized import LocalizedStr


class TestLocalizedStr:
    def test_locale(self) -> None:
        string = "Hallo, wereld!"
        locale = Locale("nl")
        sut = LocalizedStr(string, locale=locale)
        assert sut == string
        assert sut.locale is locale
