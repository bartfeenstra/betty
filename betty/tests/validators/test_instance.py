from __future__ import annotations

import pytest

from betty.validation import Invalid
from betty.validators.instance import is_instance


def test_is_instance__with_instance() -> None:
    class MyClass:
        pass

    instance = MyClass()
    assert is_instance(MyClass)(instance) == instance


def test_is_instance__without_instance() -> None:
    class MyClass:
        pass

    with pytest.RaisesGroup(Invalid):
        assert is_instance(MyClass)(object())
