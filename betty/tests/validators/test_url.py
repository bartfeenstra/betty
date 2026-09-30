from __future__ import annotations

from typing import Any

import pytest

from betty.validation import Invalid
from betty.validators.url import is_url


def test_is_url() -> None:
    assert is_url()("https://example.com") == "https://example.com"


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
def test_is_url__with_invalid_value(value: Any) -> None:
    with pytest.RaisesGroup(Invalid):
        is_url()(value)
