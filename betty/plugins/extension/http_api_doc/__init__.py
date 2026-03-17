"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final, override

from betty.asset import AssetDefinition
from betty.extension import ExtensionDefinition
from betty.link import LinkDefinition
from betty.locale.localizable.gettext import _
from betty.plugins.asset.http_api_doc import HttpApiDoc as HttpApiDocAsset
from betty.plugins.extension.webpack import Webpack
from betty.plugins.extension.webpack.build import EntryPointProvider
from betty.plugins.link.http_api_doc import HttpApiDoc as HttpApiDocLink

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
        AssetDefinition: HttpApiDocAsset,
        ExtensionDefinition: Webpack,
        LinkDefinition: HttpApiDocLink,
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
