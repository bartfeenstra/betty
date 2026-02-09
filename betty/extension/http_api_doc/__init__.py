"""Integrate Betty with `Swagger UI <https://swagger.io/tools/swagger-ui>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.extension import ExtensionDefinition
from betty.extension.webpack import Webpack
from betty.extension.webpack.build import EntryPointProvider
from betty.html import NavigationLink, NavigationLinkProvider
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
@ExtensionDefinition(
    "http-api-doc",
    label="HTTP API Documentation",
    description=_(
        "Display the HTTP API documentation in a user-friendly way using Swagger UI."
    ),
    depends_on={Webpack},
    assets_directory=Path(__file__).parent / "assets",
)
class HttpApiDoc(EntryPointProvider[Project], NavigationLinkProvider, Manufacturable):
    """
    .. plugin:: extension:http-api-doc.
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(services=project)

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()

    @override
    def secondary_navigation_links(self) -> Sequence[NavigationLink]:
        return [
            NavigationLink("betty-static:///api/index.html", _("API documentation")),
        ]
