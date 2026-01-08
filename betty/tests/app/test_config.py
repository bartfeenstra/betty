from babel import Locale

from betty.app.config import AppConfiguration
from betty.test_utils.data import HasDataTestBase


class TestAppConfiguration(HasDataTestBase[AppConfiguration]):
    sut_cls = AppConfiguration

    def test___init____minimal_locale(self) -> None:
        sut = AppConfiguration()
        assert sut.locale is None

    def test___init____with_locale(self) -> None:
        locale = Locale("nl", "NL")
        sut = AppConfiguration(locale=locale)
        assert sut.locale is locale

    def test_locale(self) -> None:
        sut = AppConfiguration()
        locale = Locale("nl", "NL")
        sut.locale = locale
        assert sut.locale is locale
