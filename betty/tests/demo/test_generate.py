from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.demo.generate import generate_with_cleanup

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.job import Context
    from betty.project import Project


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_generate_with_cleanup__without_error(
    mocker: MockerFixture, isolated_project: Project
) -> None:
    async def _generate(project: Project, *, context: Context | None = None) -> None:
        project.output_directory.mkdir(parents=True)

    m_generate = mocker.patch("betty.project.generate.generate")
    m_generate.side_effect = _generate
    (isolated_project.directory / "sentinel").touch()
    await generate_with_cleanup(isolated_project)
    assert isolated_project.directory.is_dir()
    assert isolated_project.output_directory.is_dir()
    assert not (isolated_project.directory / "sentinel").exists()


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_generate_with_cleanup__with_error(
    mocker: MockerFixture, isolated_project: Project
) -> None:
    error_message = "generation error"

    async def _generate(project: Project, *, context: Context | None = None) -> None:
        project.output_directory.mkdir(parents=True)
        raise RuntimeError(error_message)

    m_generate = mocker.patch("betty.project.generate.generate")
    m_generate.side_effect = _generate
    with pytest.raises(RuntimeError, match=error_message):
        await generate_with_cleanup(isolated_project)
    assert not isolated_project.directory.exists()
