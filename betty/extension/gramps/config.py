"""
Configuration for the :py:class:`betty.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar

from betty.ancestry.event_type import EventTypeDefinition
from betty.ancestry.place_type import PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.data import Data, Sample
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import (
    MappingProperty,
    Optional,
    Property,
    SequenceProperty,
)
from betty.data.sample import Size
from betty.data.str import StrDefinition
from betty.exception import HumanFacingException
from betty.gramps.loader import (
    DEFAULT_EVENT_TYPE_MAPPING,
    DEFAULT_PLACE_TYPE_MAPPING,
    DEFAULT_PRESENCE_ROLE_MAPPING,
)
from betty.locale.localizable.gettext import _
from betty.pathlib import FilePathDefinition
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.config import (
    PluginConfiguration,
    ResolvablePluginConfiguration,
    resolve_plugin_configuration_mapping,
)
from betty.plugin.data import PluginConfigurationDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.ancestry.event_type import EventType
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.presence_role import PresenceRole
    from betty.locale.localizable import LocalizableLike
_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class _PluginMappingProperty(
    MappingProperty[
        MutableMapping[str, PluginConfiguration[_PluginDefinitionT, _PluginT]],
        Mapping[str, ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT]],
    ]
):
    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],
        gramps_label: LocalizableLike,
        default: Mapping[
            str, ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT]
        ],
    ):
        super().__init__(
            MappingDefinition(
                cls=dict,
                key=StrDefinition(label=gramps_label),
                value=PluginConfigurationDefinition(plugin_type),
                label=plugin_type.type().label_plural,
            ),
            default=lambda: resolve_plugin_configuration_mapping(default),  # ty:ignore[invalid-argument-type]
        )


@final
@ObjectDefinition(
    label=_("Family tree configuration"),
    samples=[
        lambda: Sample(
            FamilyTreeConfiguration(name="my-gramps-family-tree"),
            label="Minimal",
            size=Size.MINIMAL,
        )
    ],
)
class FamilyTreeConfiguration(Data):
    """
    Configure a single Gramps family tree.

    .. data:: betty.extension.gramps.config:FamilyTreeConfiguration
    """

    event_types = _PluginMappingProperty(
        EventTypeDefinition,
        _("Gramps event type"),
        DEFAULT_EVENT_TYPE_MAPPING,  # ty:ignore[invalid-argument-type]
    )
    """
    How to map event types.
    """

    file = Optional(Property(FilePathDefinition(), label=_("File")))
    """
    The path to a Gramps family tree file.
    """

    name = Optional(Property(StrDefinition(label=_("Name"))))
    """
    The family tree's name in Gramps.
    """

    place_types = _PluginMappingProperty(
        PlaceTypeDefinition,
        _("Gramps place type"),
        DEFAULT_PLACE_TYPE_MAPPING,  # ty:ignore[invalid-argument-type]
    )
    """
    How to map place types.
    """

    presence_roles = _PluginMappingProperty(
        PresenceRoleDefinition,
        _("Gramps role"),
        DEFAULT_PRESENCE_ROLE_MAPPING,  # ty:ignore[invalid-argument-type]
    )
    """
    How to map presence roles.
    """

    def __init__(
        self,
        file: Path | None = None,
        name: str | None = None,
        event_types: Mapping[
            str, ResolvablePluginConfiguration[EventTypeDefinition, EventType]
        ]
        | None = None,
        place_types: Mapping[
            str, ResolvablePluginConfiguration[PlaceTypeDefinition, PlaceType]
        ]
        | None = None,
        presence_roles: Mapping[
            str, ResolvablePluginConfiguration[PresenceRoleDefinition, PresenceRole]
        ]
        | None = None,
    ):
        super().__init__()
        self.file = file
        self.name = name
        self.source  # noqa: B018
        if event_types is not None:
            self.event_types.update(event_types)  # ty:ignore[no-matching-overload]
        if place_types is not None:
            self.place_types.update(place_types)  # ty:ignore[no-matching-overload]
        if presence_roles is not None:
            self.presence_roles.update(presence_roles)  # ty:ignore[no-matching-overload]

    @property
    def source(self) -> Path | str:
        """
        The family tree's source.

        This is either the name of a family tree in Gramps, or the path to a Gramps family tree file.
        """
        if self.file is not None:
            return self.file
        if self.name is not None:
            return self.name
        raise HumanFacingException(
            _('Family tree configuration must either have a "file" or a "name"')
        )


@final
@ObjectDefinition(
    label=_("Gramps configuration"),
    samples=[
        lambda: Sample(GrampsConfiguration(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            GrampsConfiguration(executable=Path("gramps.exe")),
            label="A custom Gramps executable",
        ),
        lambda: Sample(
            GrampsConfiguration(
                family_trees=[
                    FamilyTreeConfiguration(file=Path("./gramps.gpkg")),
                ]
            ),
            label="Load a family tree from a file",
        ),
        lambda: Sample(
            GrampsConfiguration(
                family_trees=[
                    FamilyTreeConfiguration(name="my-family-tree"),
                ]
            ),
            label="Load a family tree by its name directly from Gramps",
        ),
        lambda: Sample(
            GrampsConfiguration(
                family_trees=[
                    FamilyTreeConfiguration(
                        name="my-family-tree",
                        event_types={
                            "GrampsEventType": PluginConfiguration("betty-event-type"),
                        },
                    ),
                ]
            ),
            label="Map a Gramps event type to a Betty event type",
        ),
        lambda: Sample(
            GrampsConfiguration(
                family_trees=[
                    FamilyTreeConfiguration(
                        name="my-family-tree",
                        place_types={
                            "GrampsPlaceType": PluginConfiguration("betty-place-type"),
                        },
                    ),
                ]
            ),
            label="Map a Gramps place type to a Betty place type",
        ),
        lambda: Sample(
            GrampsConfiguration(
                family_trees=[
                    FamilyTreeConfiguration(
                        name="my-family-tree",
                        event_types={
                            "GrampsRole": PluginConfiguration("betty-presence-role"),
                        },
                    ),
                ]
            ),
            label="Map a Gramps role to a Betty presence role",
        ),
    ],
)
class GrampsConfiguration(Data):
    """
    Configuration for the :py:class:`betty.extension.gramps.Gramps` extension.

    .. data:: betty.extension.gramps.config:GrampsConfiguration
    """

    family_trees = SequenceProperty(
        SequenceDefinition(
            cls=list, value=FamilyTreeConfiguration, label=_("Family trees")
        ),
        default=list,
        omit_load=True,
        omit_dump=lambda data: not len(data),
    )
    """
    The Gramps family trees to load.
    """

    executable = Optional(Property(FilePathDefinition()))
    """
    The path to a specific Gramps executable.

    Leave ``None`` to use Gramps from the PATH.
    """

    def __init__(
        self,
        *,
        family_trees: Iterable[FamilyTreeConfiguration] | None = None,
        executable: Path | None = None,
    ):
        super().__init__()
        if family_trees is not None:
            self.family_trees = family_trees
        self.executable = executable
