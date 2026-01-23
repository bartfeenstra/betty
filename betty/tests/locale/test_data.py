from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.data import LocaleDefinition


class TestLocaleDefinition:
    def test_load(self) -> None:
        sut = LocaleDefinition()
        assert sut.load(DEFAULT_LOCALE_TAG) == DEFAULT_LOCALE

    def test_dump(self) -> None:
        sut = LocaleDefinition()
        assert sut.dump(DEFAULT_LOCALE) == DEFAULT_LOCALE_TAG
