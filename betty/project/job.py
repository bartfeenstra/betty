"""
Job API integration for projects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.job import Context as JobContext

if TYPE_CHECKING:
    from betty.cache import Cache
    from betty.progress import Progress
    from betty.project import Project


class ProjectContext(JobContext):
    """
    A job context for a project.
    """

    def __init__(
        self,
        project: Project,
        *,
        cache: Cache[Any] | None = None,
        progress: Progress | None = None,
    ):
        super().__init__(cache=cache, progress=progress)
        self._project = project

    @property
    def project(self) -> Project:
        """
        The Betty project this job context is run within.
        """
        return self._project
