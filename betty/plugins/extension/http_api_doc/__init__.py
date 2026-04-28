"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.dirs import DATA_DIRECTORY
from betty.extension import ExtensionDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.asset_directory.http_api_doc import (
    HTTP_API_DOC as HTTP_API_DOC_ASSET,
)
from betty.plugins.extension.webpack import Webpack
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.plugins.link.http_api_doc import HTTP_API_DOC as HTTP_API_DOC_LINK
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


@final
@ExtensionDefinition(
    "http-api-doc",
    label="HTTP API Documentation",
    description=_(
        "Display the HTTP API documentation in a user-friendly way using Swagger UI."
    ),
    requires={
        Project.asset_directories.require(HTTP_API_DOC_ASSET),
        Project.extensions.require(Webpack),
        Project.links.require(HTTP_API_DOC_LINK),
    },
)
class HttpApiDoc(EntryPointProvider):
    """
    .. plugin:: extension:http-api-doc.
    """

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return DATA_DIRECTORY / "webpack" / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
