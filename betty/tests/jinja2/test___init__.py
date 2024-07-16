from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
from aiofiles.tempfile import TemporaryDirectory

from betty.jinja2 import Jinja2Renderer, _Citer, Jinja2Provider
from betty.model.ancestry import (
    Citation,
    HasFileReferences,
)
from betty.project import Project
from betty.tests import TemplateTestCase
from betty.tests.model.test___init__ import DummyEntity

if TYPE_CHECKING:
    from betty.app import App


class TestJinja2Provider:
    async def test_globals(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.globals, dict)

    async def test_filters(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.filters, dict)

    async def test_tests(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.tests, dict)

    async def test_new_context_vars(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.new_context_vars(), dict)


class TestJinja2Renderer:
    async def test_render_file(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = Jinja2Renderer(project.jinja2_environment, project.configuration)
            template = "{% if true %}true{% endif %}"
            expected_output = "true"
            async with TemporaryDirectory() as working_directory_path_str:
                working_directory_path = Path(working_directory_path_str)
                template_file_path = working_directory_path / "betty.txt.j2"
                async with aiofiles.open(template_file_path, "w") as f:
                    await f.write(template)
                await sut.render_file(template_file_path)
                async with aiofiles.open(working_directory_path / "betty.txt") as f:
                    assert expected_output == (await f.read()).strip()
                assert not template_file_path.exists()

    async def test_file_extensions(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = Jinja2Renderer(project.jinja2_environment, project.configuration)
            sut.file_extensions  # noqa B018


class DummyHasFileReferencesEntity(HasFileReferences, DummyEntity):
    pass


class TestGlobalCiter(TemplateTestCase):
    async def test_cite(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        assert sut.cite(citation1) == 1
        assert sut.cite(citation2) == 2
        assert sut.cite(citation1) == 1

    async def test_iter(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert [(1, citation1), (2, citation2)] == list(sut)

    async def test_len(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert len(sut) == 2
