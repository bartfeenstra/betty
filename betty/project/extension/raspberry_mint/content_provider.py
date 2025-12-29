"""
Dynamic content.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Self, TypeAlias, final

from typing_extensions import override

from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_bool,
    assert_enum,
    assert_int,
    assert_mapping,
    assert_or,
    assert_record,
    assert_sequence,
)
from betty.config import Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.attr import RequiredLocalizableAttr
from betty.locale.localizable.config import dump_localizable
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName, assert_machine_name
from betty.model import EntityDefinition
from betty.model.config import EntityReferenceSequence
from betty.plugin import Plugin
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
    PluginInstanceConfigurationSequenceSequence,
    ShorthandPluginInstanceConfigurationSequence,
    ShorthandPluginInstanceConfigurationSequenceSequence,
)
from betty.plugin.resolve import resolve_id
from betty.project.extension.raspberry_mint import (
    Breakpoint,
    JustifyContent,
    RaspberryMint,
)
from betty.project.extension.raspberry_mint import ColorStyle as RaspberryMintColorStyle
from betty.project.factory import (
    CallbackProjectDependentFactory,
    ProjectDependentSelfFactory,
)
from betty.requirement import HasRequirement, Requirement
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, MutableSequence

    from betty.document import Document
    from betty.jinja2 import Environment
    from betty.locale.localizable import LocalizableLike
    from betty.model import Entity
    from betty.plugin.repository import PluginRepository
    from betty.plugin.resolve import ResolvableId
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping
    from betty.service.level import ServiceLevel
    from betty.service.level.factory import AnyFactoryTarget


class _Base(HasRequirement, Plugin[ContentProviderDefinition]):
    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await RaspberryMint.requirement_for(
            services, cls.plugin().reference_label_with_type
        )


class SectionConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.project.extension.raspberry_mint.content_provider.Section`.
    """

    heading = RequiredLocalizableAttr("heading")

    def __init__(
        self,
        content: ShorthandPluginInstanceConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ],
        *,
        heading: LocalizableLike,
        name: MachineName | None = None,
        visually_hide_heading: bool = False,
    ):
        super().__init__()
        self.heading = ensure_localizable(heading)
        self._content = PluginInstanceConfigurationSequence(content)
        self.name = name
        self.visually_hide_heading = visually_hide_heading

    @property
    def content(
        self,
    ) -> PluginInstanceConfigurationSequence[
        ContentProviderDefinition, ContentProvider
    ]:
        """
        The content within this section.
        """
        return self._content

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("name", assert_machine_name()),
                RequiredField("heading", assert_load_localizable),
                RequiredField("content", PluginInstanceConfigurationSequence.load),
                OptionalField(
                    "visually_hide_heading",
                    assert_bool(),
                ),
            )(dump)
        )

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


@ContentProviderDefinition("raspberry-mint-section", label=_("Section"))
class Section(
    Template,
    _Base,
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
            configuration=SectionConfiguration(
                PluginInstanceConfiguration("my-first-plugin"), name="", heading="-"
            )
            if configuration is None
            else configuration,
            jinja2_environment=jinja2_environment,
        )

    @override
    @classmethod
    def configuration_cls(cls) -> type[SectionConfiguration]:
        return SectionConfiguration

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
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        return {
            "section_name": self.configuration.name,
            "section_heading": self.configuration.heading,
            "section_visually_hide_heading": self.configuration.visually_hide_heading,
            "section_content_provider_configurations": self.configuration.content,
        }


@ContentProviderDefinition(
    "raspberry-mint-featured-entities", label=_("Featured entities")
)
class FeaturedEntities(
    Template,
    _Base,
    ProjectDependentSelfFactory,
    ConfigurationDependentSelfFactory[EntityReferenceSequence],
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
    async def new_for_project(cls, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment, project=project)

    @override
    @classmethod
    def configuration_cls(cls) -> type[EntityReferenceSequence]:
        return EntityReferenceSequence

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
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        entity_types = await self._project.plugins(EntityDefinition)
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


@ContentProviderDefinition("raspberry-mint-families", label=_("Families"))
class Families(Template, _Base, ProjectDependentSelfFactory):
    """
    A person's families.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition(
    "raspberry-mint-media",
    label=_("Media"),
    description=_("A single file in a media display"),
)
class Media(Template, _Base, ProjectDependentSelfFactory):
    """
    A single file in a media display.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition(
    "raspberry-mint-media-gallery",
    label=_("Media gallery"),
    description=_("Multiple files in a media gallery display"),
)
class MediaGallery(Template, _Base, ProjectDependentSelfFactory):
    """
    Multiple files in a media gallery display.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@final
class ColorStyleConfiguration(Configuration):
    """
    Component background configuration.
    """

    def __init__(
        self,
        content: ShorthandPluginInstanceConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ],
        *,
        style: RaspberryMintColorStyle = RaspberryMintColorStyle.LIGHT,
    ):
        super().__init__()
        self.style = style
        self._content = PluginInstanceConfigurationSequence(content)

    @property
    def content(
        self,
    ) -> PluginInstanceConfigurationSequence[
        ContentProviderDefinition, ContentProvider
    ]:
        """
        The content within this color style.
        """
        return self._content

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("style", assert_enum(RaspberryMintColorStyle)),
                RequiredField("content", PluginInstanceConfigurationSequence.load),
            )(dump)
        )

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "style": self.style.value,
            "content": self.content.dump(),
        }

    @override
    def get_mutables(self) -> Iterable[object]:
        return self.content


@ContentProviderDefinition("raspberry-mint-color-style", label=_("Color style"))
class ColorStyle(
    Template, _Base, ConfigurationDependentSelfFactory[ColorStyleConfiguration]
):
    """
    Change the color style for all containing content.
    """

    @override
    @classmethod
    def configuration_cls(cls) -> type[ColorStyleConfiguration]:
        return ColorStyleConfiguration

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
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        return {
            "color_style": self.configuration.style.value,
            "color_style_content_provider_configurations": self.configuration.content,
        }


@ContentProviderDefinition("raspberry-mint-external-links", label=_("External links"))
class ExternalLinks(Template, _Base, ProjectDependentSelfFactory):
    """
    External links.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition("raspberry-mint-timeline", label=_("Timeline"))
class Timeline(Template, _Base, ProjectDependentSelfFactory):
    """
    A timeline of events.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition(
    "raspberry-mint-facts",
    label=_("Facts"),
    description=_(
        "Other entities that reference a citation or source to back up their claims."
    ),
)
class Facts(Template, _Base, ProjectDependentSelfFactory):
    """
    A list of facts.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


class PresencesConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.project.extension.raspberry_mint.content_provider.Presences`.
    """

    def __init__(
        self,
        *,
        include: Collection[ResolvableId[PresenceRoleDefinition]] | None = None,
        exclude: Collection[ResolvableId[PresenceRoleDefinition]] | None = None,
    ):
        super().__init__()
        self._include = (
            None
            if include is None
            else tuple(resolve_id(include_id) for include_id in include)
        )
        self._exclude = (
            None
            if exclude is None
            else tuple(resolve_id(exclude_id) for exclude_id in exclude)
        )

    @property
    def include(self) -> Sequence[MachineName] | None:
        """
        The presence role IDs for which to include presences.
        """
        return self._include

    @property
    def exclude(self) -> Sequence[MachineName] | None:
        """
        The presence role IDs for which to exclude presences.
        """
        return self._exclude

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        assert_ids = assert_sequence(assert_machine_name())
        return cls(
            **assert_or(
                assert_record(RequiredField("include", assert_ids)),
                assert_record(RequiredField("exclude", assert_ids)),
            )(dump)
        )

    @override
    def dump(self) -> Dump:
        dump: DumpMapping[Dump] = {}
        if self.include:
            dump["include"] = list(self.include)
        if self.exclude:
            dump["exclude"] = list(self.exclude)
        return dump


@ContentProviderDefinition("raspberry-mint-presences", label=_("Presences"))
class Presences(
    Template, _Base, ConfigurationDependentSelfFactory[PresencesConfiguration]
):
    """
    People's presences at an event.
    """

    @private
    def __init__(
        self,
        *,
        jinja2_environment: Environment,
        presence_roles: PluginRepository[PresenceRoleDefinition],
        configuration: PresencesConfiguration | None = None,
    ):
        super().__init__(
            configuration=PresencesConfiguration()
            if configuration is None
            else configuration,
            jinja2_environment=jinja2_environment,
        )
        self._presence_roles = presence_roles

    @override
    @classmethod
    def configuration_cls(cls) -> type[PresencesConfiguration]:
        return PresencesConfiguration

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: PresencesConfiguration
    ) -> AnyFactoryTarget[Self]:
        async def _factory(project: Project) -> Self:
            return cls(
                configuration=configuration,
                jinja2_environment=await project.jinja2_environment,
                presence_roles=await project.plugins(PresenceRoleDefinition),
            )

        return CallbackProjectDependentFactory(_factory)

    @override
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        include: Collection[MachineName]
        if self.configuration.include is not None:
            include = self.configuration.include
        else:
            include = {role.id for role in self._presence_roles}
            if self.configuration.exclude is not None:
                include -= set(self.configuration.exclude)
        return {
            "include": include,
        }


ColumnsWidth: TypeAlias = Mapping[Breakpoint, Sequence[int]]
ShorthandColumnsWidth: TypeAlias = (
    int | Sequence[int] | Mapping[Breakpoint, int] | ColumnsWidth
)


class ColumnsConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.project.extension.raspberry_mint.content_provider.Columns`.
    """

    def __init__(
        self,
        content: ShorthandPluginInstanceConfigurationSequenceSequence[
            ContentProviderDefinition, ContentProvider
        ],
        *,
        width: ShorthandColumnsWidth | None = None,
        justify_content: JustifyContent | None = None,
    ):
        super().__init__()
        self._content = PluginInstanceConfigurationSequenceSequence(content)
        if width is None:
            width = {Breakpoint.XS: [12]}
        elif isinstance(width, int):
            width = {Breakpoint.XS: [width]}
        elif isinstance(width, Mapping):
            width = {
                breakpoint: [columns] if isinstance(columns, int) else columns
                for breakpoint, columns in width.items()  # noqa A001
            }
        else:
            width = {Breakpoint.XS: width}

        self._width = width
        self._justify_content = justify_content

    @property
    def content(
        self,
    ) -> PluginInstanceConfigurationSequenceSequence[
        ContentProviderDefinition, ContentProvider
    ]:
        """
        The content within the columns.
        """
        return self._content

    @property
    def width(self) -> ColumnsWidth:
        """
        The column widths.
        """
        return self._width

    @property
    def justify_content(self) -> JustifyContent | None:
        """
        If and how to justify content.
        """
        return self._justify_content

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            **assert_record(
                RequiredField(
                    "content", PluginInstanceConfigurationSequenceSequence.load
                ),
                OptionalField("justify_content", assert_enum(JustifyContent)),
                OptionalField(
                    "width",
                    assert_or(
                        assert_or(
                            assert_int(),
                            assert_sequence(assert_int()),
                        ),
                        assert_or(
                            assert_mapping(assert_int(), assert_enum(Breakpoint)),
                            assert_mapping(
                                assert_sequence(assert_int()), assert_enum(Breakpoint)
                            ),
                        ),
                    ),
                ),
            )(dump)
        )

    @override
    def dump(self) -> Dump:
        dump: DumpMapping[Dump] = {
            "content": self.content.dump(),
            "width": {
                breakpoint.value: widths  # type: ignore[misc]
                for breakpoint, widths in self.width.items()  # noqa A001
            },
        }
        if self.justify_content is not None:
            dump["justify_content"] = self.justify_content.value
        return dump


@ContentProviderDefinition("raspberry-mint-columns", label=_("Columns"))
class Columns(Template, _Base, ConfigurationDependentSelfFactory[ColumnsConfiguration]):
    """
    A container with one or more columns.
    """

    @override
    @classmethod
    def configuration_cls(cls) -> type[ColumnsConfiguration]:
        return ColumnsConfiguration

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: ColumnsConfiguration
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
            "content": self.configuration.content,
            "justify_content": self.configuration.justify_content,
            "width": {
                breakpoint.value: widths
                for breakpoint, widths in self.configuration.width.items()  # noqa A001
            },
        }


@ContentProviderDefinition("raspberry-mint-enclosees", label=_("Enclosees"))
class Enclosees(Template, _Base, ProjectDependentSelfFactory):
    """
    Show the places enclosed by a place document resource.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition("raspberry-mint-file-referees", label=_("File referees"))
class FileReferees(Template, _Base, ProjectDependentSelfFactory):
    """
    Show the entities referencing a document resource that is a file.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition("raspberry-mint-citations", label=_("Citations"))
class Citations(Template, _Base, ProjectDependentSelfFactory):
    """
    The citations for a document resource that is an entity.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)
