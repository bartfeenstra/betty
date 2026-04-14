"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.job import Job

if TYPE_CHECKING:
    from pathlib import Path

    from betty.gramps.loader import GrampsLoader
    from betty.job.scheduler import Scheduler


class LoadAncestry(Job):
    """
    Load Gramps data into an ancestry.
    """

    def __init__(self, *, loader: GrampsLoader, source: Path | str):
        super().__init__(self.id_for(source))
        self._loader = loader
        self._source = source

    @classmethod
    def id_for(cls, source: Path | str, /) -> str:
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
