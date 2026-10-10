from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.validators.str import NotAStr
from betty.validators.url import MissingHost, is_url

if TYPE_CHECKING:
    from betty.validation import Invalid


def test_is_url() -> None:
    assert is_url("https://example.com") == "https://example.com"


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (NotAStr, True),
        (NotAStr, False),
        (NotAStr, 456),
        (NotAStr, object()),
        (NotAStr, []),
        (NotAStr, {}),
        (MissingHost, "https://"),
    ],
)
def test_is_url__with_invalid_value(expected: type[Invalid], value: Any) -> None:
    with pytest.raises(expected):
        is_url(value)
