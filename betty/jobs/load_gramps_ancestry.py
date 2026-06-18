"""
Jobs to load Gramps ancestry data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.job import Job

if TYPE_CHECKING:
    from betty.gramps.loader import GrampsLoader
    from betty.job.scheduler import Scheduler
    from betty.pathlib import StrPath


@final
class LoadGrampsAncestry(Job):
    """
    Load Gramps data into an ancestry.
    """

    def __init__(self, *, loader: GrampsLoader, source: StrPath):
        super().__init__(self.id_for(source))
        self._loader = loader
        self._source = source

    @classmethod
    def id_for(cls, source: StrPath, /) -> str:
        """
        Get the job ID.
        """
        return f"gramps:load-ancestry:{id(type(source))}:{source!s}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        if isinstance(self._source, str):
            await self._loader.load_name(self._source)
        else:
            await self._loader.load_file(self._source)
