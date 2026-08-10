"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.asset_directories.http_api_doc import (
    http_api_doc as HTTP_API_DOC_ASSET,
)
from betty.dirs import webpack_entry_point_directory
from betty.links.http_api_doc import HTTP_API_DOC as HTTP_API_DOC_LINK
from betty.localizables.gettext import _
from betty.project import Project
from betty.service_provider import ServiceProviderDefinition
from betty.service_providers.webpack import Webpack
from betty.service_providers.webpack.build import EntryPointProvider

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.pathlib import StrPath


@final
@ServiceProviderDefinition(
    "http-api-doc",
    label="HTTP API Documentation",
    description=_(
        "Display the HTTP API documentation in a user-friendly way using Swagger UI."
    ),
    requires={
        Project.asset_directories.require(HTTP_API_DOC_ASSET),
        Project.service_providers.require(Webpack),
        Project.links.require(HTTP_API_DOC_LINK),
    },
)
class HttpApiDoc(EntryPointProvider):
    """
    .. plugin:: service-provider:http-api-doc.
    """

    @override
    @classmethod
    def webpack_entry_point_directory(cls) -> StrPath:
        return webpack_entry_point_directory / cls.plugin().id

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
