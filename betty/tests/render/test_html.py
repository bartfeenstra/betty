from collections.abc import Mapping, Sequence
from typing import Any

import pytest
from typing_extensions import override

from betty.locale import ResolvableLocale
from betty.media_type import MediaType
from betty.render import Renderer
from betty.render.html import Html
from betty.test_utils.render import RendererTestBase
from betty.url import UrlGenerator


class _TestHtmlUrlGenerator(UrlGenerator):
    @override
    def supports(self, resource: Any, /) -> bool:
        return isinstance(resource, str) and resource == "betty-test://"

    @override
    def generate(
        self,
        resource: str,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        return "GENERATED-URL-AHOY"


class TestHtml(RendererTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Renderer:
        return Html(url_generator=_TestHtmlUrlGenerator())

    async def test_media_type(self) -> None:
        Html(url_generator=_TestHtmlUrlGenerator()).media_type  # noqa: B018

    async def test_render(self) -> None:
        assert (
            await Html(url_generator=_TestHtmlUrlGenerator()).render(
                '<a href="betty-test://"></a>'
            )
            == '<a href="GENERATED-URL-AHOY"></a>'
        )
