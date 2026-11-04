"""
Jobs to generate robots.txt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final, override

from betty.file import write
from betty.job import Job
from betty.jobs.generate_www_directory import GenerateWwwDirectory

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateRobotsTxt(Job):
    """
    Generate a site's robots.txt.
    """

    _robots_txt_template: Final[str] = """Sitemap: {{{ sitemap }}}"""

    id_for: Final[str] = "generate-robots-txt"
    """
    The job ID.
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for, dependencies=[GenerateWwwDirectory.id_for])
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        url_generator = await self._project.url_generator
        rendered_robots_txt = self._robots_txt_template.replace(
            "{{{ sitemap }}}",
            url_generator.generate("betty-static:///sitemap.xml", absolute=True),
        )
        await write(self._project.www_directory / "robots.txt", rendered_robots_txt)
