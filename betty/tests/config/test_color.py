import pytest

from betty.config.color import ColorConfiguration
from betty.exception import HumanFacingException
from betty.portable import PortableData
from betty.test_utils.config import ConfigurationTestBase


class TestColorConfiguration(ConfigurationTestBase[ColorConfiguration]):
    sut_cls = ColorConfiguration

    def test_hex(self) -> None:
        hex_value = "#123456"
        sut = ColorConfiguration(hex_value)
        assert sut.hex == hex_value

    def test_load(self) -> None:
        hex_value = "#123456"
        sut = ColorConfiguration.load(hex_value)
        assert sut.hex == hex_value

    @pytest.mark.parametrize(
        "portable,",
        [
            True,
            False,
            "#",
            "#aaaaaaa",
        ],
    )
    def test_load__with_invalid_portable(self, portable: PortableData) -> None:
        with pytest.raises(HumanFacingException):
            ColorConfiguration.load(portable)

    def test_dump(self) -> None:
        hex_value = "#123456"
        sut = ColorConfiguration(hex_value)
        assert sut.dump() == hex_value
