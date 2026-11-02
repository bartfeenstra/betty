from collections.abc import Sequence

import pytest

from betty.localizables.markup import (
    Chain,
    JoinAnd,
    JoinOr,
    Lines,
    OrderedList,
    Paragraph,
    Paragraphs,
    Quote,
    UnorderedList,
    do_you_mean,
)
from betty.localizer import AnyLocalizable, Localizer, default_localizer


@pytest.mark.parametrize(
    ("expected", "available_options"),
    [
        ("There are no available options.", []),
        ("Do you mean foo?", ["foo"]),
        ("Do you mean bar, baz, or foo?", ["foo", "bar", "baz"]),
    ],
)
async def test_do_you_mean(expected: str, available_options: Sequence[str]) -> None:
    assert default_localizer.localize(do_you_mean(*available_options)) == expected


class TestLines:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo\nBar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test_localize(
        self, expected: str, localizables: Sequence[AnyLocalizable]
    ) -> None:
        sut = Lines(*localizables)
        assert sut.localize(default_localizer) == expected


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
        self, expected: str, localizables: Sequence[AnyLocalizable]
    ) -> None:
        sut = Paragraph(*localizables)
        assert sut.localize(default_localizer) == expected


class TestParagraphs:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo\n\nBar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test_localize(
        self, expected: str, localizables: Sequence[AnyLocalizable]
    ) -> None:
        sut = Paragraphs(*localizables)
        assert sut.localize(default_localizer) == expected


class TestOrderedList:
    @pytest.mark.parametrize(
        ("expected", "localizer", "localizables"),
        [
            (
                "",
                default_localizer,
                [],
            ),
            (
                "1. Foo\n2. Bar",
                default_localizer,
                ["Foo", "Bar"],
            ),
            (
                "Foo .1\nBar .2",
                Localizer("ar"),
                ["Foo", "Bar"],
            ),
            (
                "1. Foo\n   Foo2\n2. Bar\n   Bar2",
                default_localizer,
                ["Foo\nFoo2", "Bar\nBar2"],
            ),
            (
                "1.  1\n2.  2\n3.  3\n4.  4\n5.  5\n6.  6\n7.  7\n8.  8\n9.  9\n10. 10",
                default_localizer,
                [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "10",
                ],
            ),
        ],
    )
    def test_localize(
        self,
        expected: str,
        localizer: Localizer,
        localizables: Sequence[AnyLocalizable],
    ) -> None:
        sut = OrderedList(*localizables)
        assert sut.localize(localizer) == expected


class TestUnorderedList:
    @pytest.mark.parametrize(
        ("expected", "localizer", "localizables"),
        [
            (
                "",
                default_localizer,
                [],
            ),
            (
                "- Foo\n- Bar",
                default_localizer,
                [
                    "Foo",
                    "Bar",
                ],
            ),
            (
                "Foo -\nBar -",
                Localizer("ar"),
                [
                    "Foo",
                    "Bar",
                ],
            ),
            (
                "- Foo\n  Foo2\n- Bar\n  Bar2",
                default_localizer,
                [
                    "Foo\nFoo2",
                    "Bar\nBar2",
                ],
            ),
        ],
    )
    def test_localize(
        self,
        expected: str,
        localizer: Localizer,
        localizables: Sequence[AnyLocalizable],
    ) -> None:
        sut = UnorderedList(*localizables)
        assert sut.localize(localizer) == expected


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
    def test(self, expected: str, localizables: Sequence[AnyLocalizable]) -> None:
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
    def test(self, expected: str, localizables: Sequence[AnyLocalizable]) -> None:
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
    def test(self, expected: str, localizables: Sequence[AnyLocalizable]) -> None:
        sut = JoinAnd(*localizables)
        assert sut.localize(default_localizer) == expected


class TestQuote:
    def test(self) -> None:
        assert Quote("Hello, world!").localize(default_localizer) == '"Hello, world!"'
