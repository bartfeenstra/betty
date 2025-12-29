"""
Dynamic content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_record,
    assert_str,
)
from betty.config import Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.attr import RequiredLocalizableAttr
from betty.locale.localizable.config import dump_localizable
from betty.locale.localizable.gettext import _
from betty.media_type import MediaType
from betty.media_type.media_types import PLAIN_TEXT
from betty.plugin.config import (
    PluginInstanceConfigurationSequence,
    ShorthandPluginInstanceConfigurationSequence,
)
from betty.project import Project
from betty.project.factory import (
    CallbackProjectDependentFactory,
    ProjectDependentSelfFactory,
)
from betty.requirement import HasRequirement, Requirement
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.document import Document
    from betty.jinja2 import Environment
    from betty.locale.localizable import LocalizableLike
    from betty.render import RenderDispatcher
    from betty.serde.dump import Dump, DumpMapping
    from betty.service.level import ServiceLevel
    from betty.service.level.factory import AnyFactoryTarget


class RenderConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.content_provider.content_providers.Render`.
    """

    content = RequiredLocalizableAttr("text")

    def __init__(self, content: LocalizableLike, media_type: MediaType = PLAIN_TEXT, /):
        super().__init__()
        self.content = content
        self.media_type = media_type

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        record = assert_record(
            RequiredField("content", assert_load_localizable),
            OptionalField("media_type", assert_str() | MediaType),
        )(dump)
        return cls(record["content"], record.get("media_type", PLAIN_TEXT))

    @override
    def dump(self) -> Dump:
        return {
            "content": dump_localizable(self.content),
            "media_type": str(self.media_type),
        }


@ContentProviderDefinition("render", label=_("Rendered content"))
class Render(
    ConfigurationDependentSelfFactory[RenderConfiguration],
    ContentProvider,
    HasRequirement,
):
    """
    Rendered content.
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
    ) -> AnyFactoryTarget[Self]:
        async def _callback(project: Project) -> Self:
            return cls(configuration=configuration, renderer=await project.renderer)

        return CallbackProjectDependentFactory(_callback)

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
class Notes(Template, ProjectDependentSelfFactory):
    """
    Render a page resource's notes, if it has any.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@final
class BoxConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.content_provider.content_providers.Box`.
    """

    def __init__(
        self,
        content: ShorthandPluginInstanceConfigurationSequence[
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
        self._content = PluginInstanceConfigurationSequence(content)
        self.min_height = min_height
        self.max_height = max_height
        self.height = height
        self.min_width = min_width
        self.max_width = max_width
        self.width = width

    @property
    def content(
        self,
    ) -> PluginInstanceConfigurationSequence[
        ContentProviderDefinition, ContentProvider
    ]:
        """
        The content within this box.
        """
        return self._content

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            **assert_record(
                RequiredField("content", PluginInstanceConfigurationSequence.load),
                OptionalField("min_height", assert_str()),
                OptionalField("max_height", assert_str()),
                OptionalField("height", assert_str()),
                OptionalField("min_width", assert_str()),
                OptionalField("max_width", assert_str()),
                OptionalField("width", assert_str()),
            )(dump)
        )

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump: DumpMapping[Dump] = {
            "content": self.content.dump(),
        }
        if self.min_height is not None:
            dump["min_height"] = self.min_height
        if self.max_height is not None:
            dump["max_height"] = self.max_height
        if self.height is not None:
            dump["height"] = self.height
        if self.min_width is not None:
            dump["min_width"] = self.min_width
        if self.max_width is not None:
            dump["max_width"] = self.max_width
        if self.width is not None:
            dump["width"] = self.width
        return dump

    @override
    def get_mutables(self) -> Iterable[object]:
        return self.content


@final
@ContentProviderDefinition("box", label=_("Box"))
class Box(Template, ConfigurationDependentSelfFactory[BoxConfiguration]):
    """
    A box whose dimensions can be configured.
    """

    @override
    @classmethod
    def configuration_cls(cls) -> type[BoxConfiguration]:
        return BoxConfiguration

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: BoxConfiguration
    ) -> AnyFactoryTarget[Self]:
        async def _factory(project: Project) -> Self:
            return cls(
                configuration=configuration,
                jinja2_environment=await project.jinja2_environment,
            )

        return CallbackProjectDependentFactory(_factory)

    @override
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        return {
            "box_configuration": self.configuration,
        }
