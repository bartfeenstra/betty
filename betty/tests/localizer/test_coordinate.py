import pytest

from betty.localizer import CoordinateFormatter


class TestCoordinateFormatter:
    @pytest.mark.parametrize(
        ("expected", "degrees"),
        [
            ("0° 0' 0\"", 0),
            ("52° 22' 1\"", 52.367),
        ],
    )
    async def test_format_degrees(self, expected: str, degrees: float) -> None:
        assert CoordinateFormatter().format_degrees(degrees) == expected
