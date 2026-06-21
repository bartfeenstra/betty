from collections.abc import Iterable
from typing import override

import pytest
from markupsafe import Markup

from betty.content_builder import ContentBuilder, build
from betty.document import Document


class _NoneContentBuilder(ContentBuilder):
    @override
    async def build(self, *, document: Document) -> str | None:
        return None


class _SomeContentBuilder(ContentBuilder):
    @override
    async def build(self, *, document: Document) -> str | None:
        return "SOME"


@pytest.mark.parametrize(
    ("expected", "contents"),
    [
        (None, []),
        (None, [_NoneContentBuilder()]),
        (Markup("SOME"), [_SomeContentBuilder()]),
        (Markup("SOME"), [_NoneContentBuilder(), _SomeContentBuilder()]),
    ],
)
async def test_build(
    expected: Markup | None, contents: Iterable[ContentBuilder]
) -> None:
    assert await build(Document(), contents) == expected
