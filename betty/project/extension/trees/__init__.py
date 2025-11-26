"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import _
from betty.project.extension import ExtensionPlugin
from betty.project.extension.trees.jobs import _GeneratePeopleJson
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import Generator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.project import ProjectContext


@final
@ExtensionPlugin(
    "trees",
    label="Trees",
    description=_(
        'Display interactive family trees using <a href="https://cytoscape.org/">Cytoscape</a>.'
    ),
    depends_on={Webpack},
    assets_directory_path=Path(__file__).parent / "assets",
)
class Trees(Generator, EntryPointProvider):
    """
    Provide interactive family trees for use in web pages.
    """

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(_GeneratePeopleJson())

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()
