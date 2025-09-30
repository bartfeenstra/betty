from pathlib import Path

import pytest
from typing_extensions import override

from betty.job import Context
from betty.locale.localizer import Localizer
from betty.plugin import PluginDefinition
from betty.render import Renderer, RendererDefinition, SequentialRenderer
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestRendererDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return RendererDefinition


class _Renderer(Renderer):
    _file_extensions: set[str]
    _render_file_path: Path

    @override
    @property
    def file_extensions(self) -> set[str]:
        return self._file_extensions

    @override
    async def render_file(
        self,
        file_path: Path,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> Path:
        return self._render_file_path


class _RendererOne(_Renderer):
    _file_extensions = {".one"}
    _render_file_path = Path("one.html")


class _RendererTwo(_Renderer):
    _file_extensions = {".two"}
    _render_file_path = Path("two.html")


class TestSequentialRenderer:
    def test_file_extensions__without_upstreams(self) -> None:
        sut = SequentialRenderer([])
        assert sut.file_extensions == set()

    def test_file_extensions__with_upstreams(self) -> None:
        sut = SequentialRenderer([_RendererOne(), _RendererTwo()])
        assert sut.file_extensions == {".one", ".two"}

    async def test_render_file__without_upstreams(self) -> None:
        sut = SequentialRenderer([])
        await sut.render_file(Path())

    async def test_render_file__without_matching_upstream(self) -> None:
        sut = SequentialRenderer([_RendererTwo()])
        await sut.render_file(Path("something.one"))

    async def test_render_file__with_upstream(self) -> None:
        sut = SequentialRenderer([_RendererOne()])
        assert await sut.render_file(Path("something.one")) == Path("one.html")
