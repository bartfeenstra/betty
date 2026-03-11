"""
Asset plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.asset import Asset, AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.locale.localizable.gettext import _
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.plugin.discovery import ResolvableDiscovery
    from betty.project import Project


@final
@AssetDefinition("demo", label="Demo", assets=ASSETS_DIRECTORY_PATH / "demo")
class Demo(Asset):
    """
    .. plugin:: asset:demo.
    """


@final
@AssetDefinition(
    "http-api-doc",
    label="HTTP API Documentation",
    assets=ASSETS_DIRECTORY_PATH / "http-api-doc",
)
class HttpApiDoc(Asset):
    """
    .. plugin:: asset:http-api-doc.
    """


@final
@AssetDefinition("maps", label="Maps", assets=ASSETS_DIRECTORY_PATH / "maps")
class Maps(Asset):
    """
    .. plugin:: asset:maps.
    """


@require_project
def _project(project: Project, /) -> Iterable[ResolvableDiscovery[AssetDefinition]]:
    @AssetDefinition(
        "project",
        label=_("Project"),
        assets=project.assets_directory,
        after=lambda other: other != Universe.plugin().id,
        before={Universe},
    )
    class _Project(Asset):
        """
        .. plugin:: asset:project.
        """

    yield _Project


@final
@AssetDefinition("trees", label="Trees", assets=ASSETS_DIRECTORY_PATH / "trees")
class Trees(Asset):
    """
    .. plugin:: asset:trees.
    """


@final
@AssetDefinition(
    "raspberry-mint",
    label="Raspberry Mint",
    assets=ASSETS_DIRECTORY_PATH / "raspberry-mint",
    before={Maps, Trees},
)
class RaspberryMint(Asset):
    """
    .. plugin:: asset:raspberry-mint.
    """


@final
@AssetDefinition(
    "universe",
    label="Universe",
    assets=ASSETS_DIRECTORY_PATH / "universe",
    after=lambda _: True,
    auto=True,
)
class Universe(Asset):
    """
    .. plugin:: asset:universe.
    """


@final
@AssetDefinition("webpack", label="Webpack", assets=ASSETS_DIRECTORY_PATH / "webpack")
class Webpack(Asset):
    """
    .. plugin:: asset:webpack.
    """


@final
@AssetDefinition("wiki", label="Wiki", assets=ASSETS_DIRECTORY_PATH / "wiki")
class Wiki(Asset):
    """
    .. plugin:: asset:wiki.
    """
