from typing import Any

import pytest

from betty.typing import internal, public, none_void, Void, void_none, Voidable


class TestInternal:
    def test(self) -> None:
        sentinel = object()

        @internal
        def _target() -> object:
            return sentinel

        assert _target() is sentinel


class TestPublic:
    def test(self) -> None:
        sentinel = object()

        @public
        def _target() -> object:
            return sentinel

        assert _target() is sentinel


class TestNoneVoid:
    @pytest.mark.parametrize(
        ("expected", "value"),
        [
            (None, Void),
            (None, None),
            ("abc", "abc"),
        ],
    )
    def test(self, expected: Any, value: Voidable[None | str]) -> None:
        assert none_void(value) == expected


class TestVoidNone:
    @pytest.mark.parametrize(
        ("expected", "value"),
        [
            (Void, Void),
            (Void, None),
            ("abc", "abc"),
        ],
    )
    def test(self, expected: Any, value: Any) -> None:
        assert void_none(value) == expected
