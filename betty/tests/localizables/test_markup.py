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
    ResolvableLocalizable,
    UnorderedList,
    do_you_mean,
)
from betty.localizables.plain import Plain
from betty.localizer import Localizer, default_localizer


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
        self, expected: str, localizables: Sequence[ResolvableLocalizable]
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
        self, expected: str, localizables: Sequence[ResolvableLocalizable]
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
        self, expected: str, localizables: Sequence[ResolvableLocalizable]
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
                [Plain("Foo\nFoo2"), Plain("Bar\nBar2")],
            ),
            (
                "1.  1\n2.  2\n3.  3\n4.  4\n5.  5\n6.  6\n7.  7\n8.  8\n9.  9\n10. 10",
                default_localizer,
                [
                    Plain("1"),
                    Plain("2"),
                    Plain("3"),
                    Plain("4"),
                    Plain("5"),
                    Plain("6"),
                    Plain("7"),
                    Plain("8"),
                    Plain("9"),
                    Plain("10"),
                ],
            ),
        ],
    )
    def test_localize(
        self,
        expected: str,
        localizer: Localizer,
        localizables: Sequence[ResolvableLocalizable],
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
                    Plain("Foo"),
                    Plain("Bar"),
                ],
            ),
            (
                "Foo -\nBar -",
                Localizer("ar"),
                [
                    Plain("Foo"),
                    Plain("Bar"),
                ],
            ),
            (
                "- Foo\n  Foo2\n- Bar\n  Bar2",
                default_localizer,
                [
                    Plain("Foo\nFoo2"),
                    Plain("Bar\nBar2"),
                ],
            ),
        ],
    )
    def test_localize(
        self,
        expected: str,
        localizer: Localizer,
        localizables: Sequence[ResolvableLocalizable],
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
