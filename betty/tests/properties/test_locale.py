from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.properties.locale import LocaleProperty


class TestLocaleProperty:
    class _Owner:
        locale = LocaleProperty()

    def test_set(self) -> None:
        sut = self._Owner()
        sut.locale = DEFAULT_LOCALE_TAG
        assert sut.locale == DEFAULT_LOCALE
