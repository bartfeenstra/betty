"""
Dynamic content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.data import Data, Sample
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Optional, Property
from betty.data.sample import Size
from betty.data.str import StrDefinition
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import LocalizableProperty
from betty.media_type import MediaType
from betty.media_type.media_types import PLAIN_TEXT
from betty.plugin.config import (
    PluginConfiguration,
    ResolvablePluginConfigurationSequence,
)
from betty.plugin.config.property import PluginConfigurationSequenceProperty
from betty.project import Project
from betty.project.factory import require_project
from betty.requirement import HasRequirement, Requirement
from betty.service.level.factory import (
    CallbackServiceLevelDependentFactory,
    ServiceLevelDependentSelfFactory,
    ServiceLevelTarget,
)
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.document import Document
    from betty.jinja2 import Environment
    from betty.locale.localizable import LocalizableLike
    from betty.render import RenderDispatcher
    from betty.service.level import ServiceLevel


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
    media_type = Property(MediaType.data(), default=lambda: PLAIN_TEXT, omit_load=True)

    def __init__(self, /, content: LocalizableLike, media_type: MediaType = PLAIN_TEXT):
        super().__init__()
        self.content = content
        self.media_type = media_type


@ContentProviderDefinition("render", label=_("Rendered content"))
class Render(
    ConfigurationDependentSelfFactory[RenderConfiguration],
    ContentProvider,
    HasRequirement,
):
    """
    .. plugin:: content-provider:render.
    """

    @private
    def __init__(
        self, *, configuration: RenderConfiguration, renderer: RenderDispatcher
    ):
        super().__init__(configuration=configuration)
        self._renderer = renderer

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Project.requirement_for(services, str(cls))

    @override
    @classmethod
    def configuration_cls(cls) -> type[RenderConfiguration]:
        return RenderConfiguration

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: RenderConfiguration
    ) -> ServiceLevelTarget[Self]:  # ty:ignore[invalid-method-override]
        @require_project
        async def _callback(project: Project) -> Self:
            return cls(configuration=configuration, renderer=await project.renderer)

        return CallbackServiceLevelDependentFactory(_callback)

    @override
    async def provide(self, *, document: Document) -> str | None:
        return await self._renderer.render(
            self.configuration.content.localize(document.localizer),
            self.configuration.media_type,
        )


class Template(ContentProvider):
    """
    Provides content by rendering a Jinja2 template.
    """

    @private
    def __init__(self, *args: Any, jinja2_environment: Environment, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._jinja2_environment = jinja2_environment

    @override
    async def provide(self, *, document: Document) -> str | None:
        jinja2_environment = self._jinja2_environment
        rendered_content = (
            await jinja2_environment.get_template(
                f"content/{self.plugin().id}.html.j2"
            ).render_async(
                document=document,
                **await self._provide_data(document),
            )
        ).strip()
        if rendered_content:
            return rendered_content
        return None

    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        return {}


@ContentProviderDefinition("notes", label=_("Notes"))
class Notes(Template, ServiceLevelDependentSelfFactory):
    """
    .. plugin:: content-provider:notes.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, services: Project, /) -> Self:
        return cls(jinja2_environment=await services.jinja2_environment)


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
class Box(Template, ConfigurationDependentSelfFactory[BoxConfiguration]):
    """
    .. plugin:: content-provider:box.
    """

    @override
    @classmethod
    def configuration_cls(cls) -> type[BoxConfiguration]:
        return BoxConfiguration

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: BoxConfiguration
    ) -> ServiceLevelTarget[Self]:  # ty:ignore[invalid-method-override]
        @require_project
        async def _factory(project: Project) -> Self:
            return cls(
                configuration=configuration,
                jinja2_environment=await project.jinja2_environment,
            )

        return CallbackServiceLevelDependentFactory(_factory)

    @override
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        return {
            "box_configuration": self.configuration,
        }
