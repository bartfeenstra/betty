"""
Dynamic content.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.ancestry.has_notes import HasNotes
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.data import Data, Sample
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Optional, Property
from betty.data.str import StrDefinition
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import LocalizableProperty
from betty.locale.localize import resolve_localized
from betty.media_type import MediaType
from betty.media_type.media_types import PLAIN_TEXT
from betty.plugin.config import (
    PluginConfiguration,
    ResolvablePluginConfigurationSequence,
)
from betty.plugin.config.property import PluginConfigurationSequenceProperty
from betty.sample import Size
from betty.service.level import DataManufacturable, Manufacturable
from betty.service.requirement.project import require_project
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, MutableSequence

    from betty.document import Document
    from betty.jinja2 import Environment
    from betty.locale.localizable import ResolvableLocalizable
    from betty.project import Project
    from betty.render import RenderDispatcher


@final
@ObjectDefinition(
    label=_("Rendered content configuration"),
    samples=[
        lambda: Sample(
            RenderConfiguration("Hello, world!"), label="Minimal", size=Size.MINIMAL
        )
    ],
)
class RenderConfiguration(Data):
    """
    Configuration for :py:class:`betty.content_provider.content_providers.Render`.

    .. data:: betty.content_provider.content_providers:RenderConfiguration
    """

    content = LocalizableProperty(label=_("Content"))
    media_type = Property(MediaType, default=lambda: PLAIN_TEXT, omit_load=True)

    def __init__(
        self, /, content: ResolvableLocalizable, media_type: MediaType = PLAIN_TEXT
    ):
        super().__init__()
        self.content = content
        self.media_type = media_type


@ContentProviderDefinition("render", label=_("Rendered content"))
class Render(DataManufacturable[RenderConfiguration], ContentProvider):
    """
    .. plugin:: content-provider:render.
    """

    @private
    def __init__(
        self,
        *,
        content: ResolvableLocalizable,
        renderer: RenderDispatcher,
        media_type: MediaType = PLAIN_TEXT,
    ):
        self._content = content
        self._media_type = media_type
        self._renderer = renderer

    @override
    @classmethod
    def new_data_cls(cls) -> type[RenderConfiguration]:
        return RenderConfiguration

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, data: RenderConfiguration, /) -> Self:
        return cls(
            content=data.content,
            media_type=data.media_type,
            renderer=await project.renderer,
        )

    @override
    async def provide(self, *, document: Document) -> str | None:
        return await self._renderer.render(
            resolve_localized(self._content, localizer=document.localizer),
            self._media_type,
        )


class Template(ContentProvider):
    """
    Provides content by rendering a Jinja2 template.
    """

    @private
    def __init__(self, *args: Any, jinja: Environment, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._jinja = jinja

    @override
    async def provide(self, *, document: Document) -> str | None:
        config = await self.provide_template(document)
        if config is None:
            return None
        templates: MutableSequence[str]
        if isinstance(config, str):
            templates = [config]
            data = {}
        elif isinstance(config, tuple):
            templates = [config[0]] if isinstance(config[0], str) else config[0]  # ty:ignore[invalid-assignment]
            data = config[1]
        else:
            templates = config  # ty:ignore[invalid-assignment]
            data = {}
        assert templates, "At least one template must be specified"
        rendered_content = (
            await self._jinja.select_template(templates).render_async(
                document=document,
                **data,  # ty:ignore[invalid-argument-type]
            )
        ).strip()
        if rendered_content:
            return rendered_content
        return None

    def _resolve_templates(self, templates: str | Iterable[str]) -> Iterable[str]:
        if isinstance(templates, str):
            return [templates]
        return templates

    @abstractmethod
    async def provide_template(
        self, document: Document
    ) -> str | Iterable[str] | tuple[str | Iterable[str], Mapping[str, Any]] | None:
        """
        Provide template data.

        Return a template name, a tuple of a template name and template date to render it. Return ``None`` to prevent
        anything from being rendered at all.
        """


@ContentProviderDefinition("notes", label=_("Notes"))
class Notes(Template, Manufacturable):
    """
    .. plugin:: content-provider:notes.
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def provide_template(
        self, document: Document
    ) -> str | Iterable[str] | tuple[str | Iterable[str], Mapping[str, Any]] | None:
        if isinstance(document.resource, HasNotes):
            return "component/notes.html.j2", {"notes": document.resource.notes}
        return None


@final
@ObjectDefinition(
    label=_("Box configuration"),
    samples=[
        lambda: Sample(BoxConfiguration([]), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            BoxConfiguration(
                [PluginConfiguration(Render, RenderConfiguration("Hello, world!"))],
                min_height="100px",
                max_height="1000px",
                height="500px",
                min_width="100px",
                max_width="1000px",
                width="500px",
            ),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class BoxConfiguration(Data):
    """
    Configuration for :py:class:`betty.content_provider.content_providers.Box`.

    .. data:: betty.content_provider.content_providers:BoxConfiguration
    """

    content = PluginConfigurationSequenceProperty[
        ContentProviderDefinition, ContentProvider
    ](ContentProviderDefinition, label=_("Content"))
    """
    The content within this box.
    """

    min_height = Optional(Property(StrDefinition(label=_("Minimum height"))))
    max_height = Optional(Property(StrDefinition(label=_("Maximum height"))))
    height = Optional(Property(StrDefinition(label=_("Height"))))
    min_width = Optional(Property(StrDefinition(label=_("Minimum width"))))
    max_width = Optional(Property(StrDefinition(label=_("Maximum width"))))
    width = Optional(Property(StrDefinition(label=_("Width"))))

    def __init__(
        self,
        content: ResolvablePluginConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ],
        *,
        min_height: str | None = None,
        max_height: str | None = None,
        height: str | None = None,
        min_width: str | None = None,
        max_width: str | None = None,
        width: str | None = None,
    ):
        super().__init__()
        self.content = content
        self.min_height = min_height
        self.max_height = max_height
        self.height = height
        self.min_width = min_width
        self.max_width = max_width
        self.width = width


@final
@ContentProviderDefinition("box", label=_("Box"))
class Box(Template, DataManufacturable[BoxConfiguration]):
    """
    .. plugin:: content-provider:box.
    """

    def __init__(
        self,
        *,
        content: ResolvablePluginConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ],
        jinja: Environment,
        min_height: str | None = None,
        max_height: str | None = None,
        height: str | None = None,
        min_width: str | None = None,
        max_width: str | None = None,
        width: str | None = None,
    ):
        super().__init__(jinja=jinja)
        self._content = content
        self._min_height = min_height
        self._max_height = max_height
        self._height = height
        self._min_width = min_width
        self._max_width = max_width
        self._width = width

    @override
    @classmethod
    def new_data_cls(cls) -> type[BoxConfiguration]:
        return BoxConfiguration

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, data: BoxConfiguration, /) -> Self:
        return cls(
            content=data.content,
            min_height=data.min_height,
            max_height=data.max_height,
            height=data.height,
            min_width=data.min_width,
            max_width=data.max_width,
            width=data.width,
            jinja=await project.jinja,
        )

    @override
    async def provide_template(
        self, document: Document
    ) -> str | Iterable[str] | tuple[str | Iterable[str], Mapping[str, Any]] | None:
        return "component/box.html.j2", {
            "box_content": self._content,
            "box_min_height": self._min_height,
            "box_max_height": self._max_height,
            "box_height": self._height,
            "box_min_width": self._min_width,
            "box_max_width": self._max_width,
            "box_width": self._width,
        }
