"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.dirs import ROOT_DIRECTORY
from betty.plugins.asset.http_api_doc import HTTP_API_DOC as HTTP_API_DOC_ASSET
from betty.plugins.extension.webpack import Webpack
from betty.plugins.link.http_api_doc import HTTP_API_DOC as HTTP_API_DOC_LINK
from betty.project import Project
from betty.webpack import WebpackEntryPoint, WebpackEntryPointDefinition

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
@WebpackEntryPointDefinition(
    "http-api-doc",
    requires={
        Project.assets.require(HTTP_API_DOC_ASSET),
        Project.extensions.require(Webpack),
        Project.links.require(HTTP_API_DOC_LINK),
    },
    entry_point=ROOT_DIRECTORY / "webpack-entry-points" / "webpack",
)
class HttpApiDoc(WebpackEntryPoint):
    """
    .. plugin:: extension:http-api-doc.
    """

    @override
    async def cache_keys(self) -> Sequence[str]:
        return ()
