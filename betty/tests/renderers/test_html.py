from collections.abc import Mapping, Sequence
from typing import Any, TypeGuard, override

from betty.locale import ResolvableLocale
from betty.media_type import ResolvableMediaType
from betty.renderers.html import Html
from betty.url_generator import UrlGenerator


class _TestHtmlUrlGenerator(UrlGenerator[str]):
    @override
    def supports(self, resource: Any, /) -> TypeGuard[str]:
        return isinstance(resource, str) and resource == "betty-test://"

    @override
    def generate(
        self,
        resource: str,
        /,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: ResolvableMediaType | None = None,
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
