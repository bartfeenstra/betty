"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.extension import ExtensionDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.asset.http_api_doc import HttpApiDoc
from betty.plugins.extension.webpack import Webpack
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.plugins.link.http_api_doc import HTTP_API_DOC
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
@ExtensionDefinition(
    "http-api-doc",
    label="HTTP API Documentation",
    description=_(
        "Display the HTTP API documentation in a user-friendly way using Swagger UI."
    ),
    requires={
        Project.assets.require(HttpApiDoc),
        Project.extensions.require(Webpack),
        Project.links.require(HTTP_API_DOC),
    },
)
class HttpApiDoc(EntryPointProvider):
    """
    .. plugin:: extension:http-api-doc.
    """

    # Provide an initializer without arguments so the factory can call it.
    def __init__(self):
        super().__init__()

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
