import pytest

from betty.color import ColorDefinition
from betty.exception import HumanFacingException
from betty.portable import PortableData


class TestColorDefinition:
    def test_load(self) -> None:
        color = "#123456"
        assert ColorDefinition().porter.load(color) == color

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
            ColorDefinition().porter.load(portable)

    def test_dump(self) -> None:
        color = "#123456"
        assert ColorDefinition().porter.dump(color) == color
