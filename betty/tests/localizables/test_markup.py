from collections.abc import Sequence

import pytest

from betty.localizables.markup import (
    Chain,
    JoinAnd,
    JoinOr,
    Paragraph,
    Quote,
    ResolvableLocalizable,
    do_you_mean,
)
from betty.localizer import default_localizer


@pytest.mark.parametrize(
    ("expected", "available_options"),
    [
        ("There are no available options.", []),
        ("Do you mean foo?", ["foo"]),
        ("Do you mean bar, baz, or foo?", ["foo", "bar", "baz"]),
    ],
)
async def test_do_you_mean(expected: str, available_options: Sequence[str]) -> None:
    assert do_you_mean(*available_options).localize(default_localizer) == expected


class TestParagraph:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo Bar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test_localize(
        self, expected: str, localizables: Sequence[ResolvableLocalizable]
    ) -> None:
        sut = Paragraph(*localizables)
        assert sut.localize(default_localizer) == expected


class TestChain:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "FooBar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test(
        self, expected: str, localizables: Sequence[ResolvableLocalizable]
    ) -> None:
        sut = Chain(*localizables)
        assert sut.localize(default_localizer) == expected


class TestJoinOr:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo",
                ["Foo"],
            ),
            (
                "Foo or Bar",
                ["Foo", "Bar"],
            ),
            (
                "Foo, Bar, or Baz",
                ["Foo", "Bar", "Baz"],
            ),
            (
                "Foo, Bar, Baz, or Qux",
                ["Foo", "Bar", "Baz", "Qux"],
            ),
        ],
    )
    def test(
        self, expected: str, localizables: Sequence[ResolvableLocalizable]
    ) -> None:
        sut = JoinOr(*localizables)
        assert sut.localize(default_localizer) == expected


class TestJoinAnd:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo",
                ["Foo"],
            ),
            (
                "Foo and Bar",
                ["Foo", "Bar"],
            ),
            (
                "Foo, Bar, and Baz",
                ["Foo", "Bar", "Baz"],
            ),
            (
                "Foo, Bar, Baz, and Qux",
                ["Foo", "Bar", "Baz", "Qux"],
            ),
        ],
    )
    def test(
        self, expected: str, localizables: Sequence[ResolvableLocalizable]
    ) -> None:
        sut = JoinAnd(*localizables)
        assert sut.localize(default_localizer) == expected


class TestQuote:
    def test(self) -> None:
        assert Quote("Hello, world!").localize(default_localizer) == '"Hello, world!"'
