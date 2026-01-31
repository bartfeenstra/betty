"""
Dynamic content.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Self, TypeAlias, final

from typing_extensions import override

from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.assertion import (
    assert_enum,
    assert_int,
    assert_mapping,
    assert_or,
    assert_sequence,
)
from betty.config import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.content_provider.content_providers import (
    Render,
    RenderConfiguration,
    Template,
)
from betty.data import Data, Sample, Size
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Optional, Property
from betty.data.bool import BoolDefinition
from betty.data.enum import EnumDefinition
from betty.data.int import IntDefinition
from betty.extension.raspberry_mint import (
    Breakpoint,
    JustifyContent,
    RaspberryMint,
)
from betty.extension.raspberry_mint import ColorStyle as RaspberryMintColorStyle
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import LocalizableProperty
from betty.machine_name import MachineName, MachineNameDefinition
from betty.model import EntityDefinition
from betty.model.reference import EntityReference
from betty.plugin import Plugin
from betty.plugin.config import (
    PluginConfiguration,
    ResolvablePluginConfigurationSequence,
    resolve_plugin_configuration_sequence,
)
from betty.plugin.config.property import PluginConfigurationSequenceProperty
from betty.plugin.data import PluginConfigurationSequenceDefinition, PluginIdDefinition
from betty.plugin.resolve import resolve_id
from betty.portable import CallbackPorter
from betty.project.factory import require_project
from betty.requirement import HasRequirement, Requirement
from betty.service.level.factory import (
    CallbackServiceLevelDependentFactory,
    ServiceLevelDependentSelfFactory,
)
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Collection

    from betty.ancestry import Ancestry
    from betty.document import Document
    from betty.jinja2 import Environment
    from betty.locale.localizable import ResolvableLocalizable
    from betty.plugin.repository import PluginRepository
    from betty.plugin.resolve import ResolvableId
    from betty.project import Project
    from betty.service.level import ServiceLevel
    from betty.service.level.factory import (
        ServiceLevelTarget,
    )


class _Base(HasRequirement, Plugin[ContentProviderDefinition]):
    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await RaspberryMint.requirement_for(
            services, cls.plugin().reference_label_with_type
        )


@final
@ObjectDefinition(
    label=_("Section configuration"),
    samples=[
        lambda: Sample(
            SectionConfiguration(
                PluginConfiguration("my-first-content"),  # ty:ignore[invalid-argument-type]
                heading=DUMMY_LOCALIZABLE,
            ),
            label="Minimal",
            size=Size.MINIMAL,
        ),
    ],
)
class SectionConfiguration(Data):
    """
    Configuration for :py:class:`betty.extension.raspberry_mint.content_provider.Section`.

    .. data:: betty.extension.raspberry_mint.content_provider:SectionConfiguration
    """

    content = PluginConfigurationSequenceProperty[
        ContentProviderDefinition, ContentProvider
    ](ContentProviderDefinition, label=_("Content"))
    """
    The content within this section.
    """

    heading = LocalizableProperty(label=_("Heading"))
    """
    The section heading.
    """

    name = Optional(
        Property(
            MachineNameDefinition(),
            label=_("Name"),
            omit_dump=lambda data: data is None,
        )
    )
    """
    The section's machine name, used to generate permanent links.
    """

    visually_hide_heading = Optional(
        Property(
            BoolDefinition(label=_("Visually hide heading")),
            omit_dump=lambda data: data is False,
        )
    )
    """
    Visually hide the heading.
    
    This keeps the heading for accessibility purposes, but does not display it visually.
    """

    def __init__(
        self,
        content: ResolvablePluginConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ],
        *,
        heading: ResolvableLocalizable,
        name: MachineName | None = None,
        visually_hide_heading: bool = False,
    ):
        super().__init__()
        self.content = content
        self.heading = heading
        self.name = name
        self.visually_hide_heading = visually_hide_heading


@ContentProviderDefinition("raspberry-mint-section", label=_("Section"))
class Section(
    Template,
    _Base,
    ConfigurationDependentSelfFactory[SectionConfiguration],
):
    """
    .. plugin:: content-provider:raspberry-mint-section.
    """

    @override
    @classmethod
    def configuration_cls(cls) -> type[SectionConfiguration]:
        return SectionConfiguration

    @override
    @classmethod
    def new_for_configuration(
        cls, configuration: SectionConfiguration
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
    ) -> ServiceLevelTarget[Self]:  # ty:ignore[invalid-method-override]
        @require_project
        async def _factory(project: Project) -> Self:
            return cls(
                ancestry=project.ancestry,
                configuration=configuration,
                entity_types=await project.plugins(EntityDefinition),
                jinja2_environment=await project.jinja2_environment,
            )

        return CallbackServiceLevelDependentFactory(_factory)

    @override
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        return {
            "entity": self._ancestry[self._entity_types.get(self.configuration.type)][
                self.configuration.id
            ],
        }


@ContentProviderDefinition("raspberry-mint-families", label=_("Families"))
class Families(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    A person's families.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition(
    "raspberry-mint-media",
    label=_("Media"),
    description=_("A single file in a media display"),
)
class Media(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    A single file in a media display.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition(
    "raspberry-mint-media-gallery",
    label=_("Media gallery"),
    description=_("Multiple files in a media gallery display"),
)
class MediaGallery(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    Multiple files in a media gallery display.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@final
@ObjectDefinition(
    label=_("Color style configuration"),
    samples=[
        lambda: Sample(
            ColorStyleConfiguration(
                "my-first-content", style=RaspberryMintColorStyle.DARK
            ),
            label="Default",
        )
    ],
)
class ColorStyleConfiguration(Data):
    """
    Configuration for :py:class:`betty.extension.raspberry_mint.content_provider.ColorStyle`.

    .. data:: betty.extension.raspberry_mint.content_provider:ColorStyleConfiguration
    """

    content = PluginConfigurationSequenceProperty[
        ContentProviderDefinition, ContentProvider
    ](ContentProviderDefinition, label=_("Content"))
    """
    The content within this color style.
    """

    style = Property(EnumDefinition(cls=RaspberryMintColorStyle, label=_("Style")))
    """
    The style.
    """

    def __init__(
        self,
        content: ResolvablePluginConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ],
        *,
        style: RaspberryMintColorStyle,
    ):
        super().__init__()
        self.style = style
        self.content = content


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
            "color_style": self.configuration.style.value,
            "color_style_content_provider_configurations": self.configuration.content,
        }


@ContentProviderDefinition("raspberry-mint-external-links", label=_("External links"))
class ExternalLinks(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    External links.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition("raspberry-mint-timeline", label=_("Timeline"))
class Timeline(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    A timeline of events.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition(
    "raspberry-mint-facts",
    label=_("Facts"),
    description=_(
        "Other entities that reference a citation or source to back up their claims."
    ),
)
class Facts(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    A list of facts.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@final
@ObjectDefinition(
    label=_("Presences configuration"),
    samples=[
        lambda: Sample(PresencesConfiguration(), label="Minimal"),
        lambda: Sample(
            PresencesConfiguration(include=["subject"]),
            label="Includes",
            size=Size.FULL,
        ),
        lambda: Sample(
            PresencesConfiguration(exclude=["subject"]),
            label="Excludes",
            size=Size.FULL,
        ),
    ],
)
class PresencesConfiguration(Data):
    """
    Configuration for :py:class:`betty.extension.raspberry_mint.content_provider.Presences`.

    .. data:: betty.extension.raspberry_mint.content_provider:PresencesConfiguration
    """

    exclude = Optional(
        Property(
            SequenceDefinition(
                cls=list,
                value=PluginIdDefinition(PresenceRoleDefinition),
                label=_("Exclude"),
            )
        )
    )
    """
    The presence roles for which to exclude presences.
    """

    include = Optional(
        Property(
            SequenceDefinition(
                cls=list,
                value=PluginIdDefinition(PresenceRoleDefinition),
                label=_("Include"),
            )
        )
    )
    """
    The presence roles for which to include presences.
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvableId[PresenceRoleDefinition]] | None = None,
        exclude: Iterable[ResolvableId[PresenceRoleDefinition]] | None = None,
    ):
        super().__init__()
        if include is not None:
            self.include = list(map(resolve_id, include))
        if exclude is not None:
            self.exclude = list(map(resolve_id, exclude))


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
    ) -> ServiceLevelTarget[Self]:  # ty:ignore[invalid-method-override]
        @require_project
        async def _factory(project: Project) -> Self:
            return cls(
                configuration=configuration,
                jinja2_environment=await project.jinja2_environment,
                presence_roles=await project.plugins(PresenceRoleDefinition),
            )

        return CallbackServiceLevelDependentFactory(_factory)

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


@final
@ObjectDefinition(
    label=_("Columns configuration"),
    samples=[
        lambda: Sample(
            ColumnsConfiguration(
                [PluginConfiguration(Render, RenderConfiguration("Hello, world!"))]  # ty:ignore[invalid-argument-type]
            ),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            ColumnsConfiguration(
                [PluginConfiguration(Render, RenderConfiguration("Hello, world!"))],  # ty:ignore[invalid-argument-type]
                justify_content=JustifyContent.CENTER,
            ),
            label="Justify content",
        ),
        lambda: Sample(
            ColumnsConfiguration(
                [PluginConfiguration(Render, RenderConfiguration("Hello, world!"))],  # ty:ignore[invalid-argument-type]
                width=6,
            ),
            label="A single column with a fixed, non-responsive width",
        ),
        lambda: Sample(
            ColumnsConfiguration(
                [
                    [
                        PluginConfiguration(
                            Render, RenderConfiguration("Hello, world!")
                        ),
                    ],
                    [
                        PluginConfiguration(
                            Render, RenderConfiguration("How are you?")
                        ),
                    ],
                ],
                width=[6, 6],
            ),
            label="Multiple columns with fixed, non-responsive widths",
        ),
        lambda: Sample(
            ColumnsConfiguration(
                [PluginConfiguration(Render, RenderConfiguration("Hello, world!"))],  # ty:ignore[invalid-argument-type]
                width={
                    Breakpoint.XS: 12,
                    Breakpoint.MD: 6,
                },
            ),
            label="A single column with responsive widths",
        ),
        lambda: Sample(
            ColumnsConfiguration(
                [
                    [
                        PluginConfiguration(
                            Render, RenderConfiguration("Hello, world!")
                        ),
                    ],
                    [
                        PluginConfiguration(
                            Render, RenderConfiguration("How are you?")
                        ),
                    ],
                ],
                width={
                    Breakpoint.XS: [12, 12],
                    Breakpoint.MD: [6, 6],
                },
            ),
            label="Multiple columns with responsive widths",
        ),
    ],
)
class ColumnsConfiguration(Data):
    """
    Configuration for :py:class:`betty.extension.raspberry_mint.content_provider.Columns`.

    .. data:: betty.extension.raspberry_mint.content_provider:ColumnsConfiguration
    """

    _DEFAULT_WIDTH: ColumnsWidth = {Breakpoint.XS: [12]}
    _width: ColumnsWidth

    content = Property(
        SequenceDefinition(
            cls=list,
            value=PluginConfigurationSequenceDefinition(
                ContentProviderDefinition, label=_("Column content")
            ),
            label=_("Columns"),
        )
    )
    """
    The content within the columns.
    """

    justify_content = Optional(
        Property(EnumDefinition(cls=JustifyContent, label=_("Justify content")))
    )
    """
    If and how to justify content.
    """

    width = Property(
        MappingDefinition(
            cls=dict,
            key=EnumDefinition(cls=Breakpoint, label=_("Breakpoint")),
            value=SequenceDefinition(
                cls=list,
                label=_("Column widths"),
                value=IntDefinition(label=_("Column width")),
            ),
            label=_("Breakpoints"),
            porter=CallbackPorter(
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
                lambda data: {
                    breakpoint.value: widths
                    for breakpoint, widths in data.items()  # noqa: A001
                },
            ),
        )
    )
    """
    The column widths.
    """

    def __init__(
        self,
        /,
        content: Sequence[
            ResolvablePluginConfigurationSequence[
                ContentProviderDefinition, ContentProvider
            ]
        ],
        *,
        width: ShorthandColumnsWidth | None = None,
        justify_content: JustifyContent | None = None,
    ):
        super().__init__()
        self.content = list(map(resolve_plugin_configuration_sequence, content))
        if width is None:
            self._width = self._DEFAULT_WIDTH
        elif isinstance(width, int):
            self.width = {Breakpoint.XS: [width]}
        elif isinstance(width, Mapping):
            self.width = {
                breakpoint: [columns] if isinstance(columns, int) else columns
                for breakpoint, columns in width.items()  # noqa: A001
            }
        else:
            self.width = {Breakpoint.XS: width}
        self.justify_content = justify_content


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
            "content": self.configuration.content,
            "justify_content": self.configuration.justify_content,
            "width": {
                breakpoint.value: widths
                for breakpoint, widths in self.configuration.width.items()  # noqa: A001
            },
        }


@ContentProviderDefinition("raspberry-mint-enclosees", label=_("Enclosees"))
class Enclosees(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    Show the places enclosed by a place document resource.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition("raspberry-mint-file-referees", label=_("File referees"))
class FileReferees(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    Show the entities referencing a document resource that is a file.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)


@ContentProviderDefinition("raspberry-mint-citations", label=_("Citations"))
class Citations(Template, _Base, ServiceLevelDependentSelfFactory):
    """
    The citations for a document resource that is an entity.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, project: Project, /) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)
