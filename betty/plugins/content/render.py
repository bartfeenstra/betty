"""
The render content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.attrs.localizable import LocalizableAttr
from betty.attrs.media_type import MediaTypeAttr
from betty.content import Content, ContentDefinition
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.factory import DataManufacturable
from betty.locale.localizable.gettext import _
from betty.locale.localize import resolve_localized
from betty.plugins.media_type.plain_text import PLAIN_TEXT
from betty.project import Project
from betty.property import HasProperties
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from betty.document import Document
    from betty.locale.localizable import ResolvableLocalizable
    from betty.media_type import ResolvableMediaType
    from betty.render import RenderDispatcher


@final
@ObjectDefinition(
    label=_("Rendered content configuration"),
    samples=[
        lambda: Sample(RenderData("Hello, world!"), label="Minimal", size=Size.MINIMAL)
    ],
)
class RenderData(Data, HasProperties):
    """
    Configuration for :py:class:`betty.plugins.content.render.Render`.

    .. data:: betty.plugins.content.render:RenderData
    """

    content = LocalizableAttr(label=_("Content"))
    media_type = MediaTypeAttr(omit_load=True).default(lambda: PLAIN_TEXT)

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
@ContentDefinition("render", label=_("Rendered content"))
class Render(DataManufacturable[RenderData], Content):
    """
    .. plugin:: content:render.
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
            resolve_localized(self._content, localizer=document.localizer),
            self._media_type,
        )
