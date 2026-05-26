from __future__ import annotations

from typing import Any

import pytest

from betty.assertions.url import assert_url
from betty.exception import HumanFacingException


def test_assert_url() -> None:
    assert assert_url()("https://example.com") == "https://example.com"


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        456,
        "",
        object(),
        [],
        {},
    ],
)
def test_assert_url__with_invalid_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_url()(value)
