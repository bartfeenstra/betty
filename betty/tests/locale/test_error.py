from betty.locale.error import UnknownLocale


class TestUnknownLocale:
    def test(self) -> None:
        locale = "nl-NL"
        sut = UnknownLocale(locale)
        assert locale in str(sut)
