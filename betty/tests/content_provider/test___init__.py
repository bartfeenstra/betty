from collections.abc import Iterable
from typing import override

import pytest
from markupsafe import Markup

from betty.content_provider import ContentProvider, provide_content
from betty.document import Document


class _NoneContentProvider(ContentProvider):
    @override
    async def provide(self, *, document: Document) -> str | None:
        return None


class _SomeContentProvider(ContentProvider):
    @override
    async def provide(self, *, document: Document) -> str | None:
        return "SOME"


@pytest.mark.parametrize(
    ("expected", "contents"),
    [
        (None, []),
        (None, [_NoneContentProvider()]),
        (Markup("SOME"), [_SomeContentProvider()]),
        (Markup("SOME"), [_NoneContentProvider(), _SomeContentProvider()]),
    ],
)
async def test_provide_content(
    expected: Markup | None, contents: Iterable[ContentProvider]
) -> None:
    assert await provide_content(Document(), contents) == expected
