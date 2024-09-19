from collections.abc import Sequence

import pytest
from betty.docstring import append


class TestAppend:
    @pytest.mark.parametrize(
        ("expected", "docstring", "paragraphs"),
        [
            ("", "", []),
            ("Hello, world!", "Hello, world!", []),
            ("Hello, world!", "Hello, world!\n    ", []),
            ("Hello, world!", "", ["Hello, world!"]),
            (
                "Hello, world!\n\nHello, world!",
                "Hello, world!\n    ",
                ["Hello, world!"],
            ),
            ("Hello, world!\n\nHello, world!", "", ["Hello, world!", "Hello, world!"]),
            ("Hello, world!\n\nHello, world!", "Hello, world!", ["Hello, world!"]),
            (
                "\n    Hello, world!\n\n    Hello, world!",
                "\n    Hello, world!\n    ",
                ["Hello, world!"],
            ),
            (
                "\n    Hello, world!\n      An extra indented paragraph.\n\n    Hello, world!",
                "\n    Hello, world!\n      An extra indented paragraph.",
                ["Hello, world!"],
            ),
        ],
    )
    def test(self, expected: str, docstring: str, paragraphs: Sequence[str]) -> None:
        assert append(docstring, *paragraphs) == expected
