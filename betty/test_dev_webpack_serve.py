"""
Test.
"""

# @todo REMOVE THIS FILE
from pathlib import Path

from typing_extensions import override

from betty.project import Project
from betty.project.extension.webpack.build import WatchBuildWorkspace


# @todo Finish this
class Workspace(WatchBuildWorkspace):
    """
    Test.
    """

    @override
    def watch_files(self) -> set[Path]:
        return {Path(__file__).parent / "data"}

    @override
    async def pre_build(self, project: Project) -> None:
        # @todo Finish this
        raise NotImplementedError("ooooh we are not quite here yet!")
