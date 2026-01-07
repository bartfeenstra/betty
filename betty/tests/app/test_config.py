from typing import TYPE_CHECKING

from babel import Locale

from betty.app.config import AppConfiguration
from betty.test_utils.config import ConfigurationTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping


class TestAppConfiguration(ConfigurationTestBase[AppConfiguration]):
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

    def test_load__minimal(self) -> None:
        sut = AppConfiguration()
        dump: DumpMapping[Dump] = {}
        sut.load(dump)

    def test_load__with_locale(self) -> None:
        locale = "nl"
        dump: DumpMapping[Dump] = {"locale": locale}
        sut = AppConfiguration.load(dump)
        assert sut.locale == Locale(locale)

    def test_dump__minimal(self) -> None:
        sut = AppConfiguration()
        actual = sut.dump()
        assert actual == {}

    def test_dump__with_locale(self) -> None:
        locale = "nl"
        sut = AppConfiguration(locale=Locale(locale))
        actual = sut.dump()
        assert actual == {"locale": locale}
