from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.demo.project import create_project
from betty.load import LoaderDefinition
from betty.plugins.loader.demo import Demo

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_create_project(isolated_app: App, tmp_path: Path) -> None:
    project = await create_project(isolated_app, tmp_path)
    async with project:
        assert project.directory == tmp_path
        assert Demo in (await project.service_plugins)[LoaderDefinition]
