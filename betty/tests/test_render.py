from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import aiofiles
import pytest
from typing_extensions import override

from betty.functools import unique
from betty.locale import DEFAULT_LOCALE
from betty.media_type import MediaType, UnsupportedMediaType
from betty.plugin import PluginDefinition
from betty.render import ProxyRenderer, Renderer, RendererDefinition, make_copy_function
from betty.resource import Context, new_context
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestRendererDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return RendererDefinition


class _TestRendererRenderer(Renderer):
    def __init__(self, resource_key: str):
        self._resource_key = resource_key

    @override
    @property
    def media_types(self) -> Sequence[MediaType]:
        return [MediaType("text/x.betty.test", extensions=[".test"])]

    @override
    async def render(
        self,
        content: str,
        media_type: MediaType,
        *,
        resource: Context | None = None,
    ) -> str:
        assert resource is not None
        return f"{resource['resource']}\n{resource['resource_url']}"


class _StaticRenderer(Renderer):
    MEDIA_TYPE: ClassVar[MediaType]
    RENDERED_CONTENT: ClassVar[str]

    @override
    @property
    def media_types(self) -> Sequence[MediaType]:
        return [self.MEDIA_TYPE]

    @override
    async def render(
        self,
        content: str,
        media_type: MediaType,
        *,
        resource: Context | None = None,
    ) -> str:
        return self.RENDERED_CONTENT


class _StaticRendererOne(_StaticRenderer):
    MEDIA_TYPE = MediaType("text/x.betty.test.one", extensions=[".one"])
    RENDERED_CONTENT = "ONE"


class _StaticRendererTwo(_StaticRenderer):
    MEDIA_TYPE = MediaType("text/x.betty.test.two", extensions=[".two"])
    RENDERED_CONTENT = "TWO"


class TestProxyRenderer:
    def test_media_types__without_upstreams(self) -> None:
        sut = ProxyRenderer([])
        assert sut.media_types == []

    def test_media_types__with_upstreams(self) -> None:
        renderer_one = _StaticRendererOne()
        renderer_two = _StaticRendererTwo()
        sut = ProxyRenderer([renderer_one, renderer_two])
        assert sut.media_types == list(
            unique(renderer_one.media_types, renderer_two.media_types)
        )

    async def test_render__without_upstreams(self) -> None:
        sut = ProxyRenderer([])
        with pytest.raises(UnsupportedMediaType):
            await sut.render("", _StaticRendererOne.MEDIA_TYPE)

    async def test_render__without_matching_upstream(self) -> None:
        sut = ProxyRenderer([_StaticRendererTwo()])
        with pytest.raises(UnsupportedMediaType):
            await sut.render("", _StaticRendererOne.MEDIA_TYPE)

    async def test_render__with_upstream(self) -> None:
        sut = ProxyRenderer([_StaticRendererOne()])
        assert (
            await sut.render("", _StaticRendererOne.MEDIA_TYPE)
            == _StaticRendererOne.RENDERED_CONTENT
        )


async def test_make_copy_function__www_directory(tmp_path: Path) -> None:
    sut = _TestRendererRenderer("resource")
    source_file_path = tmp_path / "source.test"
    source_file_path.touch()
    www_directory_path = tmp_path / "www"
    destination_file_path = www_directory_path / "destination.test"
    rendered_destination_file_path = www_directory_path / "destination"
    copy_function = make_copy_function(
        sut, www_directory_path=www_directory_path, resource=new_context()
    )
    await copy_function(source_file_path, destination_file_path)
    async with aiofiles.open(rendered_destination_file_path) as f:
        assert (
            await f.read()
        ).strip() == f"{rendered_destination_file_path}\nbetty:///destination"


async def test_make_copy_function__www_directory_with_hidden_file(
    tmp_path: Path,
) -> None:
    sut = _TestRendererRenderer("resource_url")
    source_file_path = tmp_path / "source.test"
    source_file_path.touch()
    www_directory_path = tmp_path / "www"
    destination_file_path = www_directory_path / ".destination.test"
    rendered_destination_file_path = www_directory_path / ".destination"
    copy_function = make_copy_function(
        sut, www_directory_path=www_directory_path, resource=new_context()
    )
    await copy_function(source_file_path, destination_file_path)
    async with aiofiles.open(rendered_destination_file_path) as f:
        assert (await f.read()).strip() == f"{rendered_destination_file_path}\nNone"


async def test_make_copy_function__www_directory_and_is_localized_and_multilingual(
    tmp_path: Path,
) -> None:
    sut = _TestRendererRenderer("resource_url")
    source_file_path = tmp_path / "source.test"
    source_file_path.touch()
    www_directory_path = tmp_path / "www"
    destination_file_path = www_directory_path / DEFAULT_LOCALE / "destination.test"
    rendered_destination_file_path = www_directory_path / DEFAULT_LOCALE / "destination"
    copy_function = make_copy_function(
        sut,
        www_directory_path=www_directory_path,
        is_localized_and_multilingual=True,
        resource=new_context(),
    )
    await copy_function(source_file_path, destination_file_path)
    async with aiofiles.open(rendered_destination_file_path) as f:
        assert (
            await f.read()
        ).strip() == f"{rendered_destination_file_path}\nbetty:///destination"
