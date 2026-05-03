from betty.datas.locale import LocaleDefinition
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG


class TestLocaleDefinition:
    def test_load(self) -> None:
        sut = LocaleDefinition()
        assert sut.porter.load(DEFAULT_LOCALE_TAG) == DEFAULT_LOCALE

    def test_dump(self) -> None:
        sut = LocaleDefinition()
        assert sut.porter.dump(DEFAULT_LOCALE) == DEFAULT_LOCALE_TAG
