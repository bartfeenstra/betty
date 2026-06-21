"""
The render content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.attrs.localizable import new_localizable_attr
from betty.attrs.media_type import new_media_type_attr
from betty.content_builder import ContentBuilder, ContentBuilderDefinition
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.factory import DataManufacturable
from betty.localizables.gettext import _
from betty.media_types.plain_text import PLAIN_TEXT
from betty.project import Project
from betty.prop import HasProps
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from betty.document import Document
    from betty.localizable import ResolvableLocalizable
    from betty.media_type import ResolvableMediaType
    from betty.render import RenderDispatcher


@final
@ObjectDefinition(
    label=_("Rendered content configuration"),
    samples=[
        lambda: Sample(RenderData("Hello, world!"), label="Minimal", size=Size.MINIMAL)
    ],
)
class RenderData(Data, HasProps):
    """
    Configuration for :py:class:`betty.content_builders.render.Render`.

    .. data:: betty.content_builders.render:RenderData
    """

    content = new_localizable_attr(label=_("Content"))
    media_type = new_media_type_attr().default(lambda: PLAIN_TEXT)

    def __init__(
        self,
        /,
        content: ResolvableLocalizable,
        media_type: ResolvableMediaType = PLAIN_TEXT,
    ):
        super().__init__()
        self.content = content
        self.media_type = media_type


@final
@ContentBuilderDefinition("render", label=_("Rendered content"))
class Render(DataManufacturable[RenderData], ContentBuilder):
    """
    .. plugin:: content-builder:render.
    """

    def __init__(
        self,
        *,
        content: ResolvableLocalizable,
        renderer: RenderDispatcher,
        media_type: ResolvableMediaType = PLAIN_TEXT,
    ):
        self._content = content
        self._media_type = media_type
        self._renderer = renderer

    @override
    @classmethod
    def new_data_cls(cls) -> type[RenderData]:
        return RenderData

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: RenderData, /) -> Self:
        return cls(
            content=data.content,
            media_type=data.media_type,
            renderer=await project.renderer,
        )

    @override
    async def build(self, *, document: Document) -> str | None:
        return await self._renderer.render(
            document.localizer.localize(self._content), self._media_type
        )
