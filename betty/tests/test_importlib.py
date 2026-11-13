from typing import Any

import pytest

from betty.importlib import fully_qualified_name, import_any
from betty.typing import Unreachable


def test_import_any__with_unknown_module_should_raise_invalid() -> None:
    with pytest.raises(ImportError):
        import_any("foo.bar:Baz")


def test_import_any__with_unknown_type_should_raise_invalid() -> None:
    with pytest.raises(ImportError):
        import_any(
            f"{test_import_any__with_unknown_type_should_raise_invalid.__module__}.Foo"
        )


def test_import_any__with_importable_should_return() -> None:
    assert (
        import_any(
            f"{test_import_any__with_importable_should_return.__module__}:{test_import_any__with_importable_should_return.__name__}"
        )
        is test_import_any__with_importable_should_return
    )


class _FullyQualifiedNameTestTarget:
    def fully_qualified_name_test_target(self) -> None:
        raise Unreachable


def _fully_qualified_name_test_target() -> None:
    pass


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
