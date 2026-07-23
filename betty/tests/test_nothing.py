from typing import Any

import pytest

from betty.nothing import Nothing


class TestNothing:
    def test___bool__(self) -> None:
        assert bool(Nothing) is False

    @pytest.mark.parametrize(
        ("expected", "other"),
        [
            (True, Nothing),
            (False, None),
            (False, False),
        ],
    )
    def test___eq__(self, expected: bool, other: Any) -> None:
        assert (Nothing == other) is expected

    def test___repr__(self) -> None:
        assert repr(Nothing) == "<Nothing>"
