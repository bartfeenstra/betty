"""
Data for the :py:class:`betty.plugins.loader.gramps.Gramps` extension.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, final

from betty.collection.mapping import MutableResolvedMapping
from betty.collection.mapping.adapter import MutableResolvedMappingAdapter
from betty.data import Data, Sample
from betty.data.aggregate.collection.mapping import MappingDefinition
from betty.data.aggregate.collection.sequence import SequenceDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.str import StrDefinition
from betty.event_type import EventTypeDefinition, EventTypeManufacturer
from betty.exception import HumanFacingException
from betty.gramps.loader import (
    DEFAULT_EVENT_TYPE_MAPPING,
    DEFAULT_PLACE_TYPE_MAPPING,
    DEFAULT_ROLE_MAPPING,
)
from betty.locale.localizable.gettext import _
from betty.pathlib import resolve_path
from betty.pathlib.data import FilePathDefinition
from betty.place_type import PlaceTypeDefinition, PlaceTypeManufacturer
from betty.plugin import PluginDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer, ResolvablePluginManufacturer
from betty.properties.collection.mapping import MappingProperty
from betty.properties.collection.sequence import SequenceProperty
from betty.property import Optional, Property
from betty.role import RoleDefinition, RoleManufacturer
from betty.sample import Size

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from betty.event_type import EventType
    from betty.locale.localizable import ResolvableLocalizable
    from betty.pathlib import StrPath
    from betty.place_type import PlaceType
    from betty.role import Role


class _PluginMappingProperty[PluginDefinitionT: PluginDefinition, PluginT: Plugin](
    MappingProperty[
        MutableMapping[str, PluginManufacturer[PluginDefinitionT, PluginT]],
        str,
        PluginManufacturer[PluginDefinitionT, PluginT],
        Mapping[str, ResolvablePluginManufacturer[PluginDefinitionT, PluginT]],
    ]
):
    def __init__(
        self,
        manufacturer: type[PluginManufacturer[PluginDefinitionT, PluginT]],
        gramps_label: ResolvableLocalizable,
        default: Mapping[str, ResolvablePluginManufacturer[PluginDefinitionT, PluginT]],
    ):
        super().__init__(
            MappingDefinition(
                cls=MutableResolvedMapping,
                factory=lambda: MutableResolvedMappingAdapter(
                    {},
                    value_resolver=manufacturer.resolve,
                ),
                key=StrDefinition(label=gramps_label),
                value=manufacturer,
                label=manufacturer.plugin_type().type().label_plural,
            ),
            default=lambda: MutableResolvedMappingAdapter(
                dict(
                    zip(
                        default.keys(),
                        manufacturer.resolve_sequence(
                            default.values(),  # ty:ignore[invalid-argument-type]
                        ),
                        strict=False,
                    )
                ),
                value_resolver=manufacturer.resolve,
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

    .. data:: betty.plugins.loader.gramps.data:FamilyTree
    """

    event_types = _PluginMappingProperty(
        EventTypeManufacturer, _("Gramps event type"), DEFAULT_EVENT_TYPE_MAPPING
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
        PlaceTypeManufacturer, _("Gramps place type"), DEFAULT_PLACE_TYPE_MAPPING
    )
    """
    How to map place types.
    """

    roles = _PluginMappingProperty(
        RoleManufacturer, _("Gramps role"), DEFAULT_ROLE_MAPPING
    )
    """
    How to map presence roles.
    """

    def __init__(
        self,
        file: StrPath | None = None,
        name: str | None = None,
        event_types: Mapping[
            str, ResolvablePluginManufacturer[EventTypeDefinition, EventType]
        ]
        | None = None,
        place_types: Mapping[
            str, ResolvablePluginManufacturer[PlaceTypeDefinition, PlaceType]
        ]
        | None = None,
        roles: Mapping[str, ResolvablePluginManufacturer[RoleDefinition, Role]]
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
        if roles is not None:
            self.roles.update(roles)  # ty:ignore[no-matching-overload]

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
            GrampsConfiguration(executable="gramps.exe"),
            label="A custom Gramps executable",
        ),
        lambda: Sample(
            GrampsConfiguration(family_trees=[FamilyTree(file="./gramps.gpkg")]),
            label="Load a family tree from a file",
        ),
        lambda: Sample(
            GrampsConfiguration(family_trees=[FamilyTree(name="my-family-tree")]),
            label="Load a family tree by its name directly from Gramps",
        ),
        lambda: Sample(
            GrampsConfiguration(
                family_trees=[
                    FamilyTree(
                        name="my-family-tree",
                        event_types={"GrampsEventType": "betty-event-type"},
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
                        place_types={"GrampsPlaceType": "betty-place-type"},
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
                        event_types={"GrampsRole": "betty-role"},
                    ),
                ]
            ),
            label="Map a Gramps role to a Betty role",
        ),
    ],
)
class GrampsConfiguration(Data):
    """
    Configuration for the :py:class:`betty.plugins.loader.gramps.Gramps` extension.

    .. data:: betty.plugins.loader.gramps.data:GrampsConfiguration
    """

    family_trees = SequenceProperty(
        SequenceDefinition(cls=list, value=FamilyTree, label=_("Family trees")),
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
        family_trees: Iterable[FamilyTree] = (),
        executable: StrPath | None = None,
    ):
        super().__init__()
        self.family_trees = family_trees
        self.executable = None if executable is None else resolve_path(executable)
