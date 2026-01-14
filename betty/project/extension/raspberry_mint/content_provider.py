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
from betty.config import Configuration, Sample
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.attr import RequiredLocalizableAttr
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.serde import dump_localizable
from betty.machine_name import MachineName, assert_machine_name
from betty.model import EntityDefinition
from betty.model.config import EntityReference
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
    from collections.abc import Collection, Iterable

    from betty.ancestry import Ancestry
    from betty.document import Document
    from betty.jinja2 import Environment
    from betty.locale.localizable import LocalizableLike
    from betty.plugin.repository import PluginRepository
    from betty.plugin.resolve import ResolvableId
    from betty.project import Project
    from betty.serde import SerializedData, SerializedMapping
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

    .. configuration:: betty.project.extension.raspberry_mint.content_provider:SectionConfiguration
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
    def load(cls, serialized: SerializedData, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("name", assert_machine_name()),
                RequiredField("heading", assert_load_localizable),
                RequiredField("content", PluginInstanceConfigurationSequence.load),
                OptionalField(
                    "visually_hide_heading",
                    assert_bool,
                ),
            )(serialized)
        )

    @override
    def dump(self) -> SerializedData:
        serialized = {
            "heading": dump_localizable(self.heading),
            "content": self.content.dump(),
        }
        if self.name:
            serialized["name"] = self.name
        if self.visually_hide_heading:
            serialized["visually_hide_heading"] = True
        return serialized

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.heading, self.content, self.name, self.visually_hide_heading) == (
            other.heading,
            other.content,
            other.name,
            other.visually_hide_heading,
        )

    @override
    def get_mutables(self) -> Iterable[object]:
        return self.heading, self._content

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

        yield Sample(
            cls(
                PluginInstanceConfiguration("my-first-content"),
                heading=DUMMY_LOCALIZABLE,
            ),
            label="Minimal",
            minimal=True,
        )


@ContentProviderDefinition("raspberry-mint-section", label=_("Section"))
class Section(
    Template,
    _Base,
    ConfigurationDependentSelfFactory[SectionConfiguration],
):
    """
    .. plugin:: content-provider:raspberry-mint-section.
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


@ContentProviderDefinition("raspberry-mint-entity-card", label=_("Entity card"))
class EntityCard(Template, ConfigurationDependentSelfFactory[EntityReference], _Base):
    """
    A card featuring an entity.
    """

    @private
    def __init__(
        self,
        *,
        ancestry: Ancestry,
        configuration: EntityReference,
        entity_types: PluginRepository[EntityDefinition],
        jinja2_environment: Environment,
    ):
        super().__init__(
            configuration=configuration,
            jinja2_environment=jinja2_environment,
        )
        self._ancestry = ancestry
        self._entity_types = entity_types

    @override
    @classmethod
    def configuration_cls(cls) -> type[EntityReference]:
        return EntityReference

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: EntityReference
    ) -> AnyFactoryTarget[Self]:
        async def _factory(project: Project) -> Self:
            return cls(
                ancestry=project.ancestry,
                configuration=configuration,
                entity_types=await project.plugins(EntityDefinition),
                jinja2_environment=await project.jinja2_environment,
            )

        return CallbackProjectDependentFactory(_factory)

    @override
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        return {
            "entity": self._ancestry[
                self._entity_types.get(self.configuration.entity_type)
            ][self.configuration.entity_id],
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
    Configuration for :py:class:`betty.project.extension.raspberry_mint.content_provider.ColorStyle`.

    .. configuration:: betty.project.extension.raspberry_mint.content_provider:ColorStyleConfiguration
    """

    def __init__(
        self,
        content: ShorthandPluginInstanceConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ],
        *,
        style: RaspberryMintColorStyle,
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
    def load(cls, serialized: SerializedData, /) -> Self:
        return cls(
            **assert_record(
                RequiredField("style", assert_enum(RaspberryMintColorStyle)),
                RequiredField("content", PluginInstanceConfigurationSequence.load),
            )(serialized)
        )

    @override
    def dump(self) -> SerializedMapping[SerializedData]:
        return {
            "style": self.style.value,
            "content": self.content.dump(),
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.style, self.content) == (other.style, other.content)

    @override
    def get_mutables(self) -> Iterable[object]:
        return self.content

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.content_provider.content_providers import Render, RenderConfiguration

        yield Sample(
            cls(
                style=RaspberryMintColorStyle.DARK,
                content=[
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("Hello, world!")
                    )
                ],
            ),
            label="Default",
        )


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

    .. configuration:: betty.project.extension.raspberry_mint.content_provider:PresencesConfiguration
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
    def load(cls, serialized: SerializedData, /) -> Self:
        assert_ids = assert_sequence(assert_machine_name())
        return cls(
            **assert_or(
                assert_record(OptionalField("include", assert_ids)),
                assert_record(OptionalField("exclude", assert_ids)),
            )(serialized)
        )

    @override
    def dump(self) -> SerializedData:
        serialized: SerializedMapping[SerializedData] = {}
        if self.include:
            serialized["include"] = list(self.include)
        if self.exclude:
            serialized["exclude"] = list(self.exclude)
        return serialized

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.include, self.exclude) == (other.include, other.exclude)

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.ancestry.presence_role.presence_roles import Subject

        yield Sample(cls(), label="Minimal")
        yield Sample(cls(include=[Subject]), label="Includes", full=True)
        yield Sample(cls(exclude=[Subject]), label="Excludes", full=True)


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

    .. configuration:: betty.project.extension.raspberry_mint.content_provider:ColumnsConfiguration
    """

    _DEFAULT_WIDTH: ColumnsWidth = {Breakpoint.XS: [12]}

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
            width = self._DEFAULT_WIDTH
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
    def load(cls, serialized: SerializedData, /) -> Self:
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
            )(serialized)
        )

    @override
    def dump(self) -> SerializedData:
        serialized: SerializedMapping[SerializedData] = {
            "content": self.content.dump(),
        }
        if self.width != self._DEFAULT_WIDTH:
            serialized["width"] = {
                breakpoint.value: widths  # type: ignore[misc]
                for breakpoint, widths in self.width.items()  # noqa A001
            }
        if self.justify_content is not None:
            serialized["justify_content"] = self.justify_content.value
        return serialized

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.content, self.width, self.justify_content) == (
            other.content,
            other.width,
            other.justify_content,
        )

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.content_provider.content_providers import Render, RenderConfiguration

        yield Sample(
            cls(
                [
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("Hello, world!")
                    )
                ]
            ),
            label="Minimal",
            minimal=True,
        )
        yield Sample(
            cls(
                [
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("Hello, world!")
                    )
                ],
                justify_content=JustifyContent.CENTER,
            ),
            label="Justify content",
        )
        yield Sample(
            cls(
                [
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("Hello, world!")
                    )
                ],
                width=6,
            ),
            label="A single column with a fixed, non-responsive width",
        )
        yield Sample(
            cls(
                [
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("Hello, world!")
                    ),
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("How are you?")
                    ),
                ],
                width=[6, 6],
            ),
            label="Multiple columns with fixed, non-responsive widths",
        )
        yield Sample(
            cls(
                [
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("Hello, world!")
                    )
                ],
                width={
                    Breakpoint.XS: 12,
                    Breakpoint.MD: 6,
                },
            ),
            label="A single column with responsive widths",
        )
        yield Sample(
            cls(
                [
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("Hello, world!")
                    ),
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("How are you?")
                    ),
                ],
                width={
                    Breakpoint.XS: [12, 12],
                    Breakpoint.MD: [6, 6],
                },
            ),
            label="Multiple columns with responsive widths",
        )


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
