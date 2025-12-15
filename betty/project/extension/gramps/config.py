"""
Provide configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar

from typing_extensions import override

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
from betty.config import Configuration
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
    from pathlib import Path

    from betty.serde.dump import Dump, DumpMapping

_PluginT = TypeVar("_PluginT", bound=Plugin)
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


_assert_gramps_type = assert_str(minimum_length=1)


@internal
class PluginMapping(Generic[_PluginDefinitionT, _PluginT], Configuration):
    """
    Map Gramps types to Betty plugin instances.
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
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            assert_mapping(
                PluginInstanceConfiguration.load,  # type: ignore[arg-type]
                _assert_gramps_type,
            )(dump)
        )

    @override
    def dump(self) -> Dump:
        return {
            gramps_type: configuration.dump()
            for gramps_type, configuration in self._mapping.items()
        }

    def __getitem__(
        self, gramps_type: str
    ) -> PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]:
        return self._mapping[gramps_type]

    def __setitem__(
        self,
        gramps_type: str,
        configuration: PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
    ) -> None:
        self.assert_mutable()
        self._mapping[gramps_type] = configuration

    def __delitem__(self, gramps_type: str) -> None:
        self.assert_mutable()
        del self._mapping[gramps_type]

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)


class EventTypeMapping(PluginMapping[EventTypeDefinition, EventType]):
    """
    Map Gramps event types to Betty event types.
    """

    _DEFAULT_MAPPING = DEFAULT_EVENT_TYPE_MAPPING


class PlaceTypeMapping(PluginMapping[PlaceTypeDefinition, PlaceType]):
    """
    Map Gramps place types to Betty place types.
    """

    _DEFAULT_MAPPING = DEFAULT_PLACE_TYPE_MAPPING


class PresenceRoleMapping(PluginMapping[PresenceRoleDefinition, PresenceRole]):
    """
    Map Gramps roles to Betty presence roles.
    """

    _DEFAULT_MAPPING = DEFAULT_PRESENCE_ROLE_MAPPING


class FamilyTreeConfiguration(Configuration):
    """
    Configure a single Gramps family tree.
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

    @override
    def get_mutables(self) -> Iterable[object]:
        return (
            self._event_types,
            self._place_types,
            self._presence_roles,
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
        self.assert_mutable()
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
    def load(cls, dump: Dump, /) -> Self:
        dump = assert_mapping()(dump)
        if (
            "file" in dump
            and "name" in dump
            or "file" not in dump
            and "name" not in dump
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
        )(dump)
        source = record.pop("source")
        return cls(source, **record)

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump = {
            "event_types": self.event_types.dump(),
            "place_types": self.place_types.dump(),
            "presence_roles": self.presence_roles.dump(),
        }
        if isinstance(self.source, str):
            dump["name"] = self.source
        else:
            dump["file"] = str(self.source)
        return dump


class FamilyTreeConfigurationSequence(ConfigurationSequence[FamilyTreeConfiguration]):
    """
    Configure zero or more Gramps family trees.
    """

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> FamilyTreeConfiguration:
        return FamilyTreeConfiguration.load(dump)


class GrampsConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
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

    @override
    def get_mutables(self) -> Iterable[object]:
        return (self._family_trees,)

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
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            **assert_record(
                OptionalField("family_trees", FamilyTreeConfigurationSequence.load),
                OptionalField("executable", assert_path()),
            )(dump)
        )

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump: DumpMapping[Dump] = {"family_trees": self.family_trees.dump()}
        if self.executable is not None:
            dump["executable"] = str(self.executable)
        return dump
