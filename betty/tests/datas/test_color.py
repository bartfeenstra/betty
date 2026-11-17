import pytest

from betty.datas.color import ColorDefinition
from betty.portable import PortableData
from betty.validation import Invalid
from betty.validators.color import NotAHex
from betty.validators.str import NotAStr


class TestColorDefinition:
    def test_load(self) -> None:
        color = "#123456"
        assert ColorDefinition().porter.load(color) == color

    @pytest.mark.parametrize(
        ("expected", "portable"),
        [
            (NotAStr, True),
            (NotAStr, False),
            (NotAHex, "#"),
            (NotAHex, "#aaaaaaa"),
        ],
    )
    def test_load__with_invalid_portable(
        self, expected: type[Invalid], portable: PortableData
    ) -> None:
        with pytest.raises(expected):
            ColorDefinition().porter.load(portable)

    def test_dump(self) -> None:
        color = "#123456"
        assert ColorDefinition().porter.dump(color) == color
