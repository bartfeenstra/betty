from betty.datas.locale import LocaleDefinition
from betty.locale import default_locale, default_locale_tag


class TestLocaleDefinition:
    def test_load(self) -> None:
        sut = LocaleDefinition()
        assert sut.porter.load(default_locale_tag) == default_locale

    def test_dump(self) -> None:
        sut = LocaleDefinition()
        assert sut.porter.dump(default_locale) == default_locale_tag
