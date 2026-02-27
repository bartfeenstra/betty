from betty.app import App
from betty.extension.spdx import Spdx, discover_licenses
from betty.plugin.discovery import discover
from betty.project import Project


async def test_discover_licenses(isolated_app: App) -> None:
    async with Project.new_isolated(isolated_app) as project:
        project.configuration.extensions.add(Spdx)
        async with project:
            await discover(
                project,
                *await discover_licenses(project),  # ty:ignore[not-iterable]
            )
