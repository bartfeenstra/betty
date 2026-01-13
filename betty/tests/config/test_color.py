import pytest

from betty.config.color import ColorConfiguration
from betty.exception import HumanFacingException
from betty.serde import SerializedData
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
        "serialized,",
        [
            True,
            False,
            "#",
            "#aaaaaaa",
        ],
    )
    def test_load__with_invalid_serialized(self, serialized: SerializedData) -> None:
        with pytest.raises(HumanFacingException):
            ColorConfiguration.load(serialized)

    def test_dump(self) -> None:
        hex_value = "#123456"
        sut = ColorConfiguration(hex_value)
        assert sut.dump() == hex_value
