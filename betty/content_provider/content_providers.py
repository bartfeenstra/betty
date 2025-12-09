"""
Dynamic content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from typing_extensions import override

from betty.assertion import RequiredField, assert_record
from betty.config import Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.html import plain_text_to_html
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.attr import RequiredLocalizableAttr
from betty.locale.localizable.config import dump_localizable
from betty.locale.localizable.gettext import _
from betty.project.factory import ProjectDependentSelfFactory
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.jinja2 import Environment
    from betty.locale.localizable import LocalizableLike
    from betty.project import Project
    from betty.resource import Context
    from betty.serde.dump import Dump
    from betty.service.level.factory import AnyFactoryTarget


class PlainTextConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.content_provider.content_providers.PlainText`.
    """

    text = RequiredLocalizableAttr("text")

    def __init__(self, text: LocalizableLike, /):
        super().__init__()
        self.text = text

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        record = assert_record(
            RequiredField("text", assert_load_localizable),
        )(dump)
        return cls(record["text"])

    @override
    def dump(self) -> Dump:
        return {
            "text": dump_localizable(self.text),
        }


@ContentProviderDefinition("plain-text", label=_("Plain text"))
class PlainText(
    ConfigurationDependentSelfFactory[PlainTextConfiguration],
    ContentProvider,
):
    """
    Plain text content.
    """

    @private
    def __init__(self, *, configuration: PlainTextConfiguration | None = None):
        super().__init__(
            configuration=PlainTextConfiguration("-")
            if configuration is None
            else configuration
        )

    @override
    @classmethod
    def configuration_cls(cls) -> type[PlainTextConfiguration]:
        return PlainTextConfiguration

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: PlainTextConfiguration
    ) -> AnyFactoryTarget[Self]:
        return lambda: cls(configuration=configuration)

    @override
    async def provide(self, *, resource: Context) -> str | None:
        return plain_text_to_html(
            self.configuration.text.localize(resource["localizer"])
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
