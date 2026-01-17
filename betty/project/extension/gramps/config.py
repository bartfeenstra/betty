"""
Configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, Self

from typing_extensions import TypeVar, override

from betty.ancestry.event_type import EventType, EventTypeDefinition
from betty.ancestry.place_type import PlaceType, PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRole, PresenceRoleDefinition
from betty.assertion import (
    OptionalField,
    assert_mapping,
    assert_path,
    assert_record,
    assert_str,
)
from betty.config import Configuration, Sample, get_full_sample
from betty.config.collections.sequence import ConfigurationSequence
from betty.exception import HumanFacingException
from betty.gramps.loader import (
    DEFAULT_EVENT_TYPE_MAPPING,
    DEFAULT_PLACE_TYPE_MAPPING,
    DEFAULT_PRESENCE_ROLE_MAPPING,
)
from betty.locale.localizable.gettext import _
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.config import PluginInstanceConfiguration
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from betty.portable import PortableData, PortableMapping

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


_assert_gramps_type = assert_str(minimum_length=1)


@internal
class PluginMapping(Configuration, Generic[_PluginDefinitionT, _PluginT]):
    """
    Map Gramps types to Betty plugin instances.

    .. configuration:: betty.project.extension.gramps.config:PluginMapping
    """

    _DEFAULT_MAPPING: Mapping[
        str, PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]
    ] = {}

    def __init__(
        self,
        mapping: Mapping[str, PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]]
        | None = None,
        /,
    ):
        super().__init__()
        self._mapping = dict(self._DEFAULT_MAPPING)
        if mapping is not None:
            self._mapping.update(mapping)

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(
            assert_mapping(
                PluginInstanceConfiguration.load,  # type: ignore[arg-type]
                _assert_gramps_type,
            )(portable)
        )

    @override
    def dump(self) -> PortableData:
        return {
            gramps_type: configuration.dump()
            for gramps_type, configuration in self._mapping.items()
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._mapping == other._mapping

    def __getitem__(
        self, gramps_type: str
    ) -> PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]:
        return self._mapping[gramps_type]

    def __setitem__(
        self,
        gramps_type: str,
        configuration: PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
    ) -> None:
        self._mapping[gramps_type] = configuration

    def __delitem__(self, gramps_type: str) -> None:
        del self._mapping[gramps_type]

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls({"GrampsType": PluginInstanceConfiguration("my-betty-type")}),
            label="Full",
            full=True,
        )


class EventTypeMapping(PluginMapping[EventTypeDefinition, EventType]):
    """
    Map Gramps event types to Betty event types.

    .. configuration:: betty.project.extension.gramps.config:EventTypeMapping
    """

    _DEFAULT_MAPPING = DEFAULT_EVENT_TYPE_MAPPING


class PlaceTypeMapping(PluginMapping[PlaceTypeDefinition, PlaceType]):
    """
    Map Gramps place types to Betty place types.

    .. configuration:: betty.project.extension.gramps.config:PlaceTypeMapping
    """

    _DEFAULT_MAPPING = DEFAULT_PLACE_TYPE_MAPPING


class PresenceRoleMapping(PluginMapping[PresenceRoleDefinition, PresenceRole]):
    """
    Map Gramps roles to Betty presence roles.

    .. configuration:: betty.project.extension.gramps.config:PresenceRoleMapping
    """

    _DEFAULT_MAPPING = DEFAULT_PRESENCE_ROLE_MAPPING


class FamilyTreeConfiguration(Configuration):
    """
    Configure a single Gramps family tree.

    .. configuration:: betty.project.extension.gramps.config:FamilyTreeConfiguration
    """

    def __init__(
        self,
        source: Path | str,
        *,
        event_types: EventTypeMapping | None = None,
        place_types: PlaceTypeMapping | None = None,
        presence_roles: PresenceRoleMapping | None = None,
    ):
        super().__init__()
        self._source = source
        self._event_types = EventTypeMapping() if event_types is None else event_types
        self._place_types = PlaceTypeMapping() if place_types is None else place_types
        self._presence_roles = (
            PresenceRoleMapping() if presence_roles is None else presence_roles
        )

    @property
    def source(self) -> Path | str:
        """
        The family tree's source.

        This is either the name of a family tree in Gramps, or the path to a Gramps family tree file.
        """
        return self._source

    @source.setter
    def source(self, source: Path | str) -> None:
        self._source = source

    @property
    def event_types(self) -> EventTypeMapping:
        """
        How to map event types.
        """
        return self._event_types

    @property
    def place_types(self) -> PlaceTypeMapping:
        """
        How to map place types.
        """
        return self._place_types

    @property
    def presence_roles(self) -> PresenceRoleMapping:
        """
        How to map presence roles.
        """
        return self._presence_roles

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        portable = assert_mapping()(portable)
        if (
            "file" in portable
            and "name" in portable
            or "file" not in portable
            and "name" not in portable
        ):
            raise HumanFacingException(
                _(
                    'Family tree configuration must contain either a "file" or a "name" key'
                )
            )
        record = assert_record(
            OptionalField("file", assert_path(), "source"),
            OptionalField("name", assert_str(), "source"),
            OptionalField("event_types", EventTypeMapping.load),
            OptionalField("place_types", PlaceTypeMapping.load),
            OptionalField("presence_roles", PresenceRoleMapping.load),
        )(portable)
        source = record.pop("source")
        return cls(source, **record)

    @override
    def dump(self) -> PortableMapping:
        serialized = {
            "event_types": self.event_types.dump(),
            "place_types": self.place_types.dump(),
            "presence_roles": self.presence_roles.dump(),
        }
        if isinstance(self.source, str):
            serialized["name"] = self.source
        else:
            serialized["file"] = str(self.source)
        return serialized

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.event_types,
            self.place_types,
            self.presence_roles,
            self.source,
        ) == (other.event_types, other.place_types, other.presence_roles, other.source)

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls("my-gramps-family-tree"), label="Minimal")


class FamilyTreeConfigurationSequence(ConfigurationSequence[FamilyTreeConfiguration]):
    """
    Configure zero or more Gramps family trees.

    .. configuration:: betty.project.extension.gramps.config:FamilyTreeConfigurationSequence
    """

    @override
    @classmethod
    def _item_cls(cls) -> type[FamilyTreeConfiguration]:
        return FamilyTreeConfiguration

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(FamilyTreeConfiguration).configuration]),
            label="Full",
            full=True,
        )


class GrampsConfiguration(Configuration):
    """
    Configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.

    .. configuration:: betty.project.extension.gramps.config:GrampsConfiguration

    ``executable``
    ^^^^^^^^^^^^^^^^
    :sup:`optional`

    The path to an existing Gramps installation on your system. Defaults to ``gramps`` on Linux and macOS, and to
    ``Gramps.exe`` on Windows.


    ``family_trees``
    ^^^^^^^^^^^^^^^^
    :sup:`required`

    An array defining zero or more Gramps family trees to load.

    If multiple family trees contain entities of the same type and with the same ID (e.g. a person with ID ``I1234``) each
    entity will overwrite any previously loaded entity.

    Each item is an object with the following keys:

    ``family_trees[].file``
    ~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`required`

    The path to a family history file. Supported file types are:

    - CSV (``.csv``)
    - GEDCOM (``.ged``)
    - GeneWeb (``.gw``)
    - Gramps package (``.gpkg``)
    - Gramps XML (``.gramps``)
    - Gramps 2.x database (``.grdb``)
    - Pro-Gen (``.def``)
    - vCard (``.vcf``)

    This is mutually exclusive with ``family_trees[].name``.

    ``family_trees[].name``
    ~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`required`

    The name of a family tree in your local Gramps installation.

    This is mutually exclusive with ``family_trees[].file``.

    ``family_trees[].event_types``
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`optional`

    How to map Gramps event types to Betty event types. Each key is a Gramps event type, and each value is the plugin ID of
    the Betty event type to import the Gramps event type as.

    ``family_trees[].place_types``
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`optional`

    How to map Gramps place types to Betty place types. Each key is a Gramps place type, and each value is the plugin ID
    of the Betty place type to import the Gramps place type as.

    ``family_trees[].presence_roles``
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :sup:`optional`

    How to map Gramps roles to Betty presence roles. Each key is a Gramps role, and each value is the plugin ID of the
    Betty presence role to import the Gramps role as.
    """

    def __init__(
        self,
        *,
        family_trees: FamilyTreeConfigurationSequence | None = None,
        executable: Path | None = None,
    ):
        super().__init__()
        self._family_trees = (
            FamilyTreeConfigurationSequence() if family_trees is None else family_trees
        )
        self._executable = executable

    @property
    def family_trees(self) -> FamilyTreeConfigurationSequence:
        """
        The Gramps family trees to load.
        """
        return self._family_trees

    @family_trees.setter
    def family_trees(self, family_trees: Iterable[FamilyTreeConfiguration]) -> None:
        self._family_trees.replace(*family_trees)

    @property
    def executable(self) -> Path | None:
        """
        The path to a specific Gramps executable.

        Leave ``None`` to use Gramps from the PATH.
        """
        return self._executable

    @executable.setter
    def executable(self, executable: Path | None) -> None:
        self._executable = executable

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("family_trees", FamilyTreeConfigurationSequence.load),
                OptionalField("executable", assert_path()),
            )(portable)
        )

    @override
    def dump(self) -> PortableMapping:
        portable: PortableMapping = {"family_trees": self.family_trees.dump()}
        if self.executable is not None:
            portable["executable"] = str(self.executable)
        return portable

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.family_trees, self.executable) == (
            other.family_trees,
            other.executable,
        )

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal")
        yield Sample(
            cls(executable=Path("gramps.exe")), label="A custom Gramps executable"
        )
        yield Sample(
            cls(
                family_trees=FamilyTreeConfigurationSequence(
                    [
                        FamilyTreeConfiguration(source=Path("./gramps.gpkg")),
                    ]
                )
            ),
            label="Load a family tree from a file",
        )
        yield Sample(
            cls(
                family_trees=FamilyTreeConfigurationSequence(
                    [
                        FamilyTreeConfiguration(source="my-family-tree"),
                    ]
                )
            ),
            label="Load a family tree by its name directly from Gramps",
        )
        yield Sample(
            cls(
                family_trees=FamilyTreeConfigurationSequence(
                    [
                        FamilyTreeConfiguration(
                            source="my-family-tree",
                            event_types=EventTypeMapping(
                                {
                                    "GrampsEventType": PluginInstanceConfiguration(
                                        "betty-event-type"
                                    ),
                                }
                            ),
                        ),
                    ]
                )
            ),
            label="Map a Gramps event type to a Betty event type",
        )
        yield Sample(
            cls(
                family_trees=FamilyTreeConfigurationSequence(
                    [
                        FamilyTreeConfiguration(
                            source="my-family-tree",
                            place_types=PlaceTypeMapping(
                                {
                                    "GrampsPlaceType": PluginInstanceConfiguration(
                                        "betty-place-type"
                                    ),
                                }
                            ),
                        ),
                    ]
                )
            ),
            label="Map a Gramps place type to a Betty place type",
        )
        yield Sample(
            cls(
                family_trees=FamilyTreeConfigurationSequence(
                    [
                        FamilyTreeConfiguration(
                            source="my-family-tree",
                            event_types=EventTypeMapping(
                                {
                                    "GrampsRole": PluginInstanceConfiguration(
                                        "betty-presence-role"
                                    ),
                                }
                            ),
                        ),
                    ]
                )
            ),
            label="Map a Gramps role to a Betty presence role",
        )
