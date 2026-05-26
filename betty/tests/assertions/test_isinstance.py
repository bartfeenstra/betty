from __future__ import annotations

import pytest

from betty.assertions.isinstance import assert_isinstance
from betty.exception import HumanFacingException


def test_assert_isinstance__with_instance() -> None:
    class MyClass:
        pass

    instance = MyClass()
    assert assert_isinstance(MyClass)(instance) == instance


def test_assert_isinstance__without_instance() -> None:
    class MyClass:
        pass

    with pytest.raises(HumanFacingException):
        assert assert_isinstance(MyClass)(object())
