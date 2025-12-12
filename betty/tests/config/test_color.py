import pytest

from betty.config.color import ColorConfiguration
from betty.exception import HumanFacingException
from betty.serde.dump import Dump


class TestColorConfiguration:
    def test_hex(self) -> None:
        hex_value = "#123456"
        sut = ColorConfiguration(hex_value)
        assert sut.hex == hex_value

    def test_load(self) -> None:
        hex_value = "#123456"
        sut = ColorConfiguration.load(hex_value)
        assert sut.hex == hex_value

    @pytest.mark.parametrize(
        "dump,",
        [
            True,
            False,
            "#",
            "#aaaaaaa",
        ],
    )
    def test_load__with_invalid_dumps(self, dump: Dump) -> None:
        with pytest.raises(HumanFacingException):
            ColorConfiguration.load(dump)

    def test_dump(self) -> None:
        hex_value = "#123456"
        sut = ColorConfiguration(hex_value)
        assert sut.dump() == hex_value
