from collections.abc import Iterable
from typing import override

import pytest
from markupsafe import Markup

from betty.content import Content, build
from betty.document import Document


class _NoneContent(Content):
    @override
    async def build(self, *, document: Document) -> str | None:
        return None


class _SomeContent(Content):
    @override
    async def build(self, *, document: Document) -> str | None:
        return "SOME"


@pytest.mark.parametrize(
    ("expected", "contents"),
    [
        (None, []),
        (None, [_NoneContent()]),
        (Markup("SOME"), [_SomeContent()]),
        (Markup("SOME"), [_NoneContent(), _SomeContent()]),
    ],
)
async def test_build(expected: Markup | None, contents: Iterable[Content]) -> None:
    assert await build(Document(), contents) == expected
