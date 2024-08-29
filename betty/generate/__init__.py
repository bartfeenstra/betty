"""
Provide the Generation API.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from contextlib import suppress
from pathlib import Path

from aiofiles.os import makedirs

from betty.job import Context
from betty.job.pool import Pool
from betty.project import Project
from betty.project import ProjectEvent


class GenerateSiteEvent(ProjectEvent):
    """
    Dispatched to generate a project's site.
    """

    def __init__(self, job_context: GenerationContext):
        super().__init__(job_context.project)
        self._job_context = job_context

    @property
    def job_context(self) -> GenerationContext:
        """
        The site generation job context.
        """
        return self._job_context


class GenerationContext(Context):
    """
    A site generation job context.
    """

    def __init__(self, project: Project):
        super().__init__()
        self._project = project

    @property
    def project(self) -> Project:
        """
        The Betty project this job context is run within.
        """
        return self._project


async def generate(project: Project) -> None:
    """
    Generate a new site.
    """
    from betty.generate.task import _generate_delegate, _generate_static_public

    logger = logging.getLogger(__name__)
    job_context = GenerationContext(project)
    app = project.app

    logger.info(
        app.localizer._("Generating your site to {output_directory}.").format(
            output_directory=project.configuration.output_directory_path
        )
    )
    with suppress(FileNotFoundError):
        await asyncio.to_thread(
            shutil.rmtree, project.configuration.output_directory_path
        )
    await makedirs(project.configuration.output_directory_path, exist_ok=True)

    # The static public assets may be overridden depending on the number of locales rendered, so ensure they are
    # generated before anything else.
    await _generate_static_public(job_context)

    # @todo Start the pool first thing in the generation workflow.
    # @todo That way workers can boot up the App/Project environment while
    # @todo we continue with things like static assets here.
    # @todo
    async with Pool(project) as process_pool:
        await _generate_delegate(project, process_pool)

    project.configuration.output_directory_path.chmod(0o755)
    for directory_path_str, subdirectory_names, file_names in os.walk(
        project.configuration.output_directory_path
    ):
        directory_path = Path(directory_path_str)
        for subdirectory_name in subdirectory_names:
            (directory_path / subdirectory_name).chmod(0o755)
        for file_name in file_names:
            (directory_path / file_name).chmod(0o644)
