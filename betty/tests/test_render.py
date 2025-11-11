from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar

import aiofiles
import pytest
from typing_extensions import override

from betty.job import Context
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import Localizer
from betty.media_type import MediaType
from betty.plugin import PluginDefinition
from betty.render import Renderer, RendererDefinition, make_copy_function
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestRendererDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return RendererDefinition


class _TestRendererRenderer(Renderer):
    @override
    @property
    def input(self) -> MediaType:
        return [MediaType("text/x.betty.test", extensions=[".test"])]

    @override
    async def render(
        self,
        content: str,
        media_type: MediaType,
        *,
        data: Mapping[str, Any] | None = None,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> str:
        assert data is not None
        page_resource = data["page_resource"]
        assert isinstance(page_resource, str)
        return page_resource


class _StaticRenderer(Renderer):
    MEDIA_TYPE: ClassVar[MediaType]
    RENDERED_CONTENT: ClassVar[str]

    @override
    @property
    def input(self) -> MediaType:
        return [self.MEDIA_TYPE]

    @override
    async def render(
        self,
        content: str,
        media_type: MediaType,
        *,
        data: Mapping[str, Any] | None = None,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> str:
        return self.RENDERED_CONTENT


class _StaticRendererOne(_StaticRenderer):
    MEDIA_TYPE = MediaType("text/x.betty.test.one", extensions=[".one"])
    RENDERED_CONTENT = "ONE"


class _StaticRendererTwo(_StaticRenderer):
    MEDIA_TYPE = MediaType("text/x.betty.test.two", extensions=[".two"])
    RENDERED_CONTENT = "TWO"



async def test_make_copy_function__www_directory(tmp_path: Path) -> None:
    sut = _TestRendererRenderer()
    source_file_path = tmp_path / "source.test"
    source_file_path.touch()
    www_directory_path = tmp_path / "www"
    destination_file_path = www_directory_path / "destination.test"
    rendered_destination_file_path = www_directory_path / "destination"
    copy_function = make_copy_function(sut, www_directory_path=www_directory_path)
    await copy_function(source_file_path, destination_file_path)
    async with aiofiles.open(rendered_destination_file_path) as f:
        assert (await f.read()).strip() == "betty:///destination"


async def test_make_copy_function__www_directory_and_is_localized_and_multilingual(
    tmp_path: Path,
) -> None:
    sut = _TestRendererRenderer()
    source_file_path = tmp_path / "source.test"
    source_file_path.touch()
    www_directory_path = tmp_path / "www"
    destination_file_path = www_directory_path / DEFAULT_LOCALE / "destination.test"
    rendered_destination_file_path = www_directory_path / DEFAULT_LOCALE / "destination"
    copy_function = make_copy_function(
        sut, www_directory_path=www_directory_path, is_localized_and_multilingual=True
    )
    await copy_function(source_file_path, destination_file_path)
    async with aiofiles.open(rendered_destination_file_path) as f:
        assert (await f.read()).strip() == "betty:///destination"
