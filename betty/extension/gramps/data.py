"""
Data for the :py:class:`betty.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, final

from betty.collections import MutableResolvedMapping, MutableResolvedMappingProxy
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
from betty.data.str import StrDefinition
from betty.event_type import EventTypeDefinition
from betty.exception import HumanFacingException
from betty.gramps.loader import (
    DEFAULT_EVENT_TYPE_MAPPING,
    DEFAULT_PLACE_TYPE_MAPPING,
    DEFAULT_PRESENCE_ROLE_MAPPING,
)
from betty.locale.localizable.gettext import _
from betty.pathlib import FilePathDefinition
from betty.place_type import PlaceTypeDefinition
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.config import (
    PluginConfiguration,
    ResolvablePluginConfiguration,
    resolve_plugin_configuration,
    resolve_plugin_configuration_mapping,
)
from betty.plugin.data import PluginConfigurationDefinition
from betty.presence_role import PresenceRoleDefinition
from betty.sample import Size

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.event_type import EventType
    from betty.locale.localizable import ResolvableLocalizable
    from betty.place_type import PlaceType
    from betty.presence_role import PresenceRole


class _PluginMappingProperty[PluginDefinitionT: PluginDefinition, PluginT: Plugin](
    MappingProperty[
        MutableMapping[str, PluginConfiguration[PluginDefinitionT, PluginT]],
        Mapping[str, ResolvablePluginConfiguration[PluginDefinitionT, PluginT]],
    ]
):
    def __init__(
        self,
        plugin_type: type[PluginDefinitionT],
        gramps_label: ResolvableLocalizable,
        default: Mapping[
            str, ResolvablePluginConfiguration[PluginDefinitionT, PluginT]
        ],
    ):
        super().__init__(
            MappingDefinition(
                cls=MutableResolvedMapping,
                factory=lambda items: MutableResolvedMappingProxy(
                    resolve_plugin_configuration_mapping(items),
                    value_resolver=resolve_plugin_configuration,
                ),
                key=StrDefinition(label=gramps_label),
                value=PluginConfigurationDefinition(plugin_type),
                label=plugin_type.type().label_plural,
            ),
            default=lambda: MutableResolvedMappingProxy(
                resolve_plugin_configuration_mapping(default),
                value_resolver=resolve_plugin_configuration,
            ),
        )


@final
@ObjectDefinition(
    label=_("Family tree"),
    samples=[
        lambda: Sample(
            FamilyTree(name="my-gramps-family-tree"), label="Minimal", size=Size.MINIMAL
        )
    ],
)
class FamilyTree(Data):
    """
    A Gramps family tree.

    .. data:: betty.extension.gramps.data:FamilyTree
    """

    event_types = _PluginMappingProperty(
        EventTypeDefinition, _("Gramps event type"), DEFAULT_EVENT_TYPE_MAPPING
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
        PlaceTypeDefinition, _("Gramps place type"), DEFAULT_PLACE_TYPE_MAPPING
    )
    """
    How to map place types.
    """

    presence_roles = _PluginMappingProperty(
        PresenceRoleDefinition, _("Gramps role"), DEFAULT_PRESENCE_ROLE_MAPPING
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
                    FamilyTree(file=Path("./gramps.gpkg")),
                ]
            ),
            label="Load a family tree from a file",
        ),
        lambda: Sample(
            GrampsConfiguration(
                family_trees=[
                    FamilyTree(name="my-family-tree"),
                ]
            ),
            label="Load a family tree by its name directly from Gramps",
        ),
        lambda: Sample(
            GrampsConfiguration(
                family_trees=[
                    FamilyTree(
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
                    FamilyTree(
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
                    FamilyTree(
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

    .. data:: betty.extension.gramps.data:GrampsConfiguration
    """

    family_trees = SequenceProperty(
        SequenceDefinition(cls=list, value=FamilyTree, label=_("Family trees")),
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
        family_trees: Iterable[FamilyTree] | None = None,
        executable: Path | None = None,
    ):
        super().__init__()
        if family_trees is not None:
            self.family_trees = family_trees
        self.executable = executable
