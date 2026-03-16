from collections.abc import Mapping, Sequence
from typing import Any, override

from betty.locale import ResolvableLocale
from betty.media_type import MediaType
from betty.plugins.renderer.html import Html
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


class TestHtml:
    async def test_media_type(self) -> None:
        Html(url_generator=_TestHtmlUrlGenerator()).media_type  # noqa: B018

    async def test_render(self) -> None:
        assert (
            await Html(url_generator=_TestHtmlUrlGenerator()).render(
                '<a href="betty-test://"></a>'
            )
            == '<a href="GENERATED-URL-AHOY"></a>'
        )
