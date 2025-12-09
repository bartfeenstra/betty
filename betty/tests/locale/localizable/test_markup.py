from collections.abc import Sequence
from gettext import NullTranslations

import pytest

from betty.locale.localizable import (
    LocalizableLike,
)
from betty.locale.localizable.markup import (
    AllEnumeration,
    AnyEnumeration,
    Chain,
    Lines,
    OrderedList,
    Paragraph,
    Paragraphs,
    UnorderedList,
    do_you_mean,
)
from betty.locale.localizable.plain import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer


@pytest.mark.parametrize(
    ("expected", "available_options"),
    [
        ("There are no available options.", []),
        ("Do you mean foo?", ["foo"]),
        ("Do you mean one of bar, baz, or foo?", ["foo", "bar", "baz"]),
    ],
)
async def test_do_you_mean(expected: str, available_options: Sequence[str]) -> None:
    assert do_you_mean(*available_options).localize(DEFAULT_LOCALIZER) == expected


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
        self, expected: str, localizables: Sequence[LocalizableLike]
    ) -> None:
        sut = Lines(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


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
        self, expected: str, localizables: Sequence[LocalizableLike]
    ) -> None:
        sut = Paragraph(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


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
        self, expected: str, localizables: Sequence[LocalizableLike]
    ) -> None:
        sut = Paragraphs(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestOrderedList:
    @pytest.mark.parametrize(
        ("expected", "localizer", "localizables"),
        [
            (
                "",
                DEFAULT_LOCALIZER,
                [],
            ),
            (
                "1. Foo\n2. Bar",
                DEFAULT_LOCALIZER,
                ["Foo", "Bar"],
            ),
            (
                "Foo .1\nBar .2",
                Localizer("ar", NullTranslations()),
                ["Foo", "Bar"],
            ),
            (
                "1. Foo\n   Foo2\n2. Bar\n   Bar2",
                DEFAULT_LOCALIZER,
                [Plain("Foo\nFoo2"), Plain("Bar\nBar2")],
            ),
            (
                "1.  1\n2.  2\n3.  3\n4.  4\n5.  5\n6.  6\n7.  7\n8.  8\n9.  9\n10. 10",
                DEFAULT_LOCALIZER,
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
        localizables: Sequence[LocalizableLike],
    ) -> None:
        sut = OrderedList(*localizables)
        assert sut.localize(localizer) == expected


class TestUnorderedList:
    @pytest.mark.parametrize(
        ("expected", "localizer", "localizables"),
        [
            (
                "",
                DEFAULT_LOCALIZER,
                [],
            ),
            (
                "- Foo\n- Bar",
                DEFAULT_LOCALIZER,
                [
                    Plain("Foo"),
                    Plain("Bar"),
                ],
            ),
            (
                "Foo -\nBar -",
                Localizer("ar", NullTranslations()),
                [
                    Plain("Foo"),
                    Plain("Bar"),
                ],
            ),
            (
                "- Foo\n  Foo2\n- Bar\n  Bar2",
                DEFAULT_LOCALIZER,
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
        localizables: Sequence[LocalizableLike],
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
    def test(self, expected: str, localizables: Sequence[LocalizableLike]) -> None:
        sut = Chain(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestAnyEnumeration:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo",
                ["Foo"],
            ),
            (
                "Foo, or Bar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test(self, expected: str, localizables: Sequence[LocalizableLike]) -> None:
        sut = AnyEnumeration(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestAllEnumeration:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo",
                ["Foo"],
            ),
            (
                "Foo, and Bar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test(self, expected: str, localizables: Sequence[LocalizableLike]) -> None:
        sut = AllEnumeration(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected
