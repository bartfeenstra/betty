"""
Configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from betty.ancestry.event_type import EventTypeDefinition
from betty.ancestry.place_type import PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.data import Data, Sample
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Optional, Property
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
from betty.plugin.config import PluginConfiguration
from betty.plugin.data import PluginConfigurationDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.ancestry.event_type import EventType
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.presence_role import PresenceRole


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

    .. data:: betty.project.extension.gramps.config:FamilyTreeConfiguration
    """

    event_types = Property(
        MappingDefinition(
            cls=dict,
            key=StrDefinition(label=_("Gramps event type")),
            item=PluginConfigurationDefinition(EventTypeDefinition),
            label=_("Event types"),
        ),
        default=lambda: dict(DEFAULT_EVENT_TYPE_MAPPING),
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

    place_types = Property(
        MappingDefinition(
            cls=dict,
            key=StrDefinition(label=_("Gramps place type")),
            item=PluginConfigurationDefinition(PlaceTypeDefinition),
            label=_("Place types"),
        ),
        default=lambda: dict(DEFAULT_PLACE_TYPE_MAPPING),
    )
    """
    How to map place types.
    """
    presence_roles = Property(
        MappingDefinition(
            cls=dict,
            key=StrDefinition(label=_("Gramps role")),
            item=PluginConfigurationDefinition(PresenceRoleDefinition),
            label=_("Presence roles"),
        ),
        default=lambda: dict(DEFAULT_PRESENCE_ROLE_MAPPING),
    )
    """
    How to map presence roles.
    """

    def __init__(
        self,
        file: Path | None = None,
        name: str | None = None,
        event_types: Mapping[str, PluginConfiguration[EventTypeDefinition, EventType]]
        | None = None,
        place_types: Mapping[str, PluginConfiguration[PlaceTypeDefinition, PlaceType]]
        | None = None,
        presence_roles: Mapping[
            str, PluginConfiguration[PresenceRoleDefinition, PresenceRole]
        ]
        | None = None,
    ):
        super().__init__()
        self.file = file
        self.name = name
        self.source  # noqa: B018
        if event_types is not None:
            self.event_types.update(event_types)
        if place_types is not None:
            self.place_types.update(place_types)
        if presence_roles is not None:
            self.presence_roles.update(presence_roles)

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
    Configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.

    .. data:: betty.project.extension.gramps.config:GrampsConfiguration
    """

    family_trees = Property(
        SequenceDefinition(
            cls=list, item=FamilyTreeConfiguration.data(), label=_("Family trees")
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
            self.family_trees.extend(family_trees)
        self.executable = executable
