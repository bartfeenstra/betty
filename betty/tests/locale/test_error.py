from betty.locale.error import InvalidLocale, UnknownLocale


class TestInvalidLocale:
    def test(self) -> None:
        locale = "my-first-locale"
        sut = InvalidLocale(locale)
        assert locale in str(sut)


class TestUnknownLocale:
    def test(self) -> None:
        locale = "nl"
        sut = UnknownLocale(locale)
        assert locale in str(sut)
