"""
Dynamic content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from typing_extensions import override

from betty.assertion import OptionalField, RequiredField, assert_record, assert_str
from betty.config import Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.attr import RequiredLocalizableAttr
from betty.locale.localizable.config import dump_localizable
from betty.locale.localizable.gettext import _
from betty.media_type import MediaType
from betty.media_type.media_types import PLAIN_TEXT
from betty.project import Project
from betty.project.factory import (
    CallbackProjectDependentFactory,
    ProjectDependentSelfFactory,
)
from betty.requirement import HasRequirement, Requirement
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.jinja2 import Environment
    from betty.locale.localizable import LocalizableLike
    from betty.render import RenderDispatcher
    from betty.resource import Context
    from betty.serde.dump import Dump
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
    async def provide(self, *, resource: Context) -> str | None:
        return await self._renderer.render(
            self.configuration.content.localize(resource.localizer),
            self.configuration.media_type,
        )


class Template(ProjectDependentSelfFactory, ContentProvider):
    """
    Provides content by rendering a Jinja2 template.
    """

    @private
    def __init__(self, *args: Any, jinja2_environment: Environment, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._jinja2_environment = jinja2_environment

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)

    @override
    async def provide(self, *, resource: Context) -> str | None:
        jinja2_environment = self._jinja2_environment
        rendered_content = (
            await jinja2_environment.get_template(
                f"content/{self.plugin().id}.html.j2"
            ).render_async(
                resource=resource,
                **await self._provide_data(resource),
            )
        ).strip()
        if rendered_content:
            return rendered_content
        return None

    async def _provide_data(self, resource: Context) -> Mapping[str, Any]:
        return {}


@ContentProviderDefinition("notes", label=_("Notes"))
class Notes(Template):
    """
    Render a page resource's notes, if it has any.
    """
