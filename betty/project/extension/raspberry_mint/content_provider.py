"""
Dynamic content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_bool,
    assert_enum,
    assert_record,
    assert_setattr,
)
from betty.config import Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProviderPlugin
from betty.content_provider.content_providers import Template
from betty.locale.localizable import (
    LocalizableLike,
    RequiredLocalizableAttr,
    _,
    ensure_localizable,
)
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.config import dump_localizable
from betty.machine_name import MachineName, assert_machine_name
from betty.model import EntityPlugin
from betty.model.config import EntityReferenceSequence
from betty.plugin import Plugin
from betty.plugin.config import PluginInstanceConfigurationSequence
from betty.project.extension.raspberry_mint import ColorStyle as RaspberryMintColorStyle
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.factory import (
    CallbackProjectDependentFactory,
    ProjectDependentSelfFactory,
)
from betty.requirement import HasRequirement, Requirement
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, MutableSequence

    from betty.content_provider.config import (
        ContentProviderInstanceConfigurationSequence,
        ShorthandContentProviderInstanceConfigurationSequence,
    )
    from betty.jinja2 import Environment
    from betty.model import Entity
    from betty.project import Project
    from betty.resource import Context
    from betty.serde.dump import Dump, DumpMapping
    from betty.service.level import ServiceLevel
    from betty.service.level.factory import AnyFactoryTarget


class _Base(Plugin, HasRequirement):
    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await RaspberryMint.requirement_for(
            services, cls.plugin.reference_label_with_type
        )


class SectionConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.project.extension.raspberry_mint.content_provider.Section`.
    """

    heading = RequiredLocalizableAttr("heading")

    def __init__(
        self,
        *,
        heading: LocalizableLike,
        content: ShorthandContentProviderInstanceConfigurationSequence = None,
        name: MachineName | None = None,
        visually_hide_heading: bool = False,
    ):
        super().__init__()
        self.heading = ensure_localizable(heading)
        self._content = PluginInstanceConfigurationSequence(content)
        self.name = name
        self.visually_hide_heading = visually_hide_heading

    @property
    def content(self) -> ContentProviderInstanceConfigurationSequence:
        """
        The content within this section.
        """
        return self._content

    @override
    def load(self, dump: Dump, /) -> None:
        assert_record(
            OptionalField("name", assert_machine_name() | assert_setattr(self, "name")),
            RequiredField(
                "heading", assert_load_localizable | assert_setattr(self, "heading")
            ),
            RequiredField("content", self.content.load),
            OptionalField(
                "visually_hide_heading",
                assert_bool() | assert_setattr(self, "visually_hide_heading"),
            ),
        )(dump)

    @override
    def dump(self) -> Dump:
        dump = {
            "heading": dump_localizable(self.heading),
            "content": self.content.dump(),
        }
        if self.name:
            dump["name"] = self.name
        if self.visually_hide_heading:
            dump["visually_hide_heading"] = True
        return dump

    @override
    def get_mutables(self) -> Iterable[object]:
        return self.heading, self._content


@ContentProviderPlugin("raspberry-mint-section", label=_("Section"))
class Section(
    Template,
    _Base,
    ProjectDependentSelfFactory,
    ConfigurationDependentSelfFactory[SectionConfiguration],
):
    """
    A section on the page with a heading and a permanent link.
    """

    @private
    def __init__(
        self,
        *,
        jinja2_environment: Environment,
        configuration: SectionConfiguration | None = None,
    ):
        super().__init__(
            configuration=SectionConfiguration(name="", heading="")
            if configuration is None
            else configuration,
            jinja2_environment=jinja2_environment,
        )

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: SectionConfiguration
    ) -> AnyFactoryTarget[Self]:
        async def _factory(project: Project) -> Self:
            return cls(
                configuration=configuration,
                jinja2_environment=await project.jinja2_environment,
            )

        return CallbackProjectDependentFactory(_factory)

    @override
    async def _provide_data(self, resource: Context) -> Mapping[str, Any]:
        return {
            "section_name": self.configuration.name,
            "section_heading": self.configuration.heading,
            "section_visually_hide_heading": self.configuration.visually_hide_heading,
            "section_content_provider_configurations": self.configuration.content,
        }


@ContentProviderPlugin("raspberry-mint-featured-entities", label=_("Featured entities"))
class FeaturedEntities(
    Template,
    ConfigurationDependentSelfFactory[EntityReferenceSequence],
    _Base,
):
    """
    Featured entities.
    """

    @private
    def __init__(
        self,
        *,
        jinja2_environment: Environment,
        project: Project,
        configuration: EntityReferenceSequence | None = None,
    ):
        super().__init__(
            configuration=EntityReferenceSequence()
            if configuration is None
            else configuration,
            jinja2_environment=jinja2_environment,
        )
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment, project=project)

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: EntityReferenceSequence
    ) -> AnyFactoryTarget[Self]:
        async def _factory(project: Project) -> Self:
            return cls(
                configuration=configuration,
                jinja2_environment=await project.jinja2_environment,
                project=project,
            )

        return CallbackProjectDependentFactory(_factory)

    @override
    async def _provide_data(self, resource: Context) -> Mapping[str, Any]:
        entity_types = await self._project.plugins(EntityPlugin)
        entities: MutableSequence[Entity] = []
        for entity in self.configuration:
            assert entity.entity_type is not None
            assert entity.entity_id is not None
            entities.append(
                self._project.ancestry[entity_types.get(entity.entity_type)][
                    entity.entity_id
                ]
            )
        return {
            "entities": entities,
        }


@ContentProviderPlugin("raspberry-mint-family", label=_("Family"))
class Family(Template, _Base):
    """
    A person's family.
    """


@ContentProviderPlugin("raspberry-mint-media", label=_("Media gallery"))
class Media(Template):
    """
    Media gallery.
    """


@final
class ColorStyleConfiguration(Configuration):
    """
    Component background configuration.
    """

    def __init__(
        self,
        style: RaspberryMintColorStyle = RaspberryMintColorStyle.LIGHT,
        *,
        content: ShorthandContentProviderInstanceConfigurationSequence = None,
    ):
        super().__init__()
        self.style = style
        self._content = PluginInstanceConfigurationSequence(content)

    @property
    def content(self) -> ContentProviderInstanceConfigurationSequence:
        """
        The content within this color style.
        """
        return self._content

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        assert_record(
            OptionalField(
                "style",
                assert_enum(RaspberryMintColorStyle) | assert_setattr(self, "style"),
            ),
            RequiredField("content", self.content.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "style": self.style.value,
            "content": self.content.dump(),
        }

    @override
    def get_mutables(self) -> Iterable[object]:
        return self.content


@ContentProviderPlugin("raspberry-mint-color-style", label=_("Color style"))
class ColorStyle(Template, ConfigurationDependentSelfFactory[ColorStyleConfiguration]):
    """
    Change the color style for all containing content.
    """

    @private
    def __init__(
        self,
        *,
        jinja2_environment: Environment,
        configuration: ColorStyleConfiguration | None = None,
    ):
        super().__init__(
            configuration=ColorStyleConfiguration()
            if configuration is None
            else configuration,
            jinja2_environment=jinja2_environment,
        )

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: ColorStyleConfiguration
    ) -> AnyFactoryTarget[Self]:
        async def _factory(project: Project) -> Self:
            return cls(
                configuration=configuration,
                jinja2_environment=await project.jinja2_environment,
            )

        return CallbackProjectDependentFactory(_factory)

    @override
    async def _provide_data(self, resource: Context) -> Mapping[str, Any]:
        return {
            "color_style": self.configuration.style.value,
            "color_style_content_provider_configurations": self.configuration.content,
        }


@ContentProviderPlugin("raspberry-mint-external-links", label=_("External links"))
class ExternalLinks(Template):
    """
    External links.
    """
