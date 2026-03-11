from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.ancestry import Ancestry
from betty.copyright_notice import CopyrightNotice
from betty.extension.demo import Demo
from betty.extension.demo.jobs import LoadAncestry
from betty.extension.demo.project import create_project
from betty.license import License
from betty.service.level.universe import UNIVERSE
from betty.test_utils.job import do

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_create_project(isolated_app: App, tmp_path: Path) -> None:
    project = await create_project(isolated_app, tmp_path)
    async with project:
        assert project.directory == tmp_path
        assert Demo in await project.extensions


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_load_ancestry() -> None:
    ancestry = Ancestry()
    await do(
        LoadAncestry(
            ancestry=ancestry,
            factory=UNIVERSE.factory,
            streetmix_copyright_notice=CopyrightNotice(),
            streetmix_license=License(),
        )
    )
    assert len(ancestry)
