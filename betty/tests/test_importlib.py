from typing import Any

import pytest

from betty.importlib import fully_qualified_name
from betty.typing import Unreachable


class _FullyQualifiedNameTestTarget:
    def fully_qualified_name_test_target(self) -> None:
        raise Unreachable


def _fully_qualified_name_test_target() -> None:
    raise Unreachable


@pytest.mark.parametrize(
    ("expected", "target"),
    [
        ("builtins:object", object),
        ("builtins:object", object()),
        (
            "betty.tests.test_importlib:_FullyQualifiedNameTestTarget",
            _FullyQualifiedNameTestTarget,
        ),
        (
            "betty.tests.test_importlib:_FullyQualifiedNameTestTarget",
            _FullyQualifiedNameTestTarget(),
        ),
        (
            "betty.tests.test_importlib:_FullyQualifiedNameTestTarget.fully_qualified_name_test_target",
            _FullyQualifiedNameTestTarget.fully_qualified_name_test_target,
        ),
        (
            "betty.tests.test_importlib:_fully_qualified_name_test_target",
            _fully_qualified_name_test_target,
        ),
    ],
)
def test_fully_qualified_name(expected: str, target: Any) -> None:
    assert fully_qualified_name(target) == expected
