"""
Provide configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar, final

from typing_extensions import override

from betty.ancestry.event_type import EventType
from betty.ancestry.place_type import PlaceType
from betty.ancestry.presence_role import PresenceRole
from betty.assertion import (
    OptionalField,
    assert_len,
    assert_mapping,
    assert_path,
    assert_record,
    assert_setattr,
    assert_str,
)
from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.exception import HumanFacingException
from betty.gramps.loader import (
    DEFAULT_EVENT_TYPES_MAPPING,
    DEFAULT_PLACE_TYPES_MAPPING,
    DEFAULT_PRESENCE_ROLES_MAPPING,
)
from betty.locale.localizable import _
from betty.plugin import ClassedPluginDefinition
from betty.plugin.config import PluginInstanceConfiguration
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, MutableMapping

    from betty.serde.dump import Dump, DumpMapping

_PluginT = TypeVar("_PluginT")
_ClassedPluginDefinitionT = TypeVar(
    "_ClassedPluginDefinitionT", bound=ClassedPluginDefinition[Any]
)


def _assert_gramps_type(value: Any) -> str:
    event_type = assert_str()(value)
    assert_len(minimum=1)(event_type)
    return event_type


@internal
@final
class PluginMapping(Generic[_ClassedPluginDefinitionT, _PluginT], Configuration):
    """
    Map Gramps types to Betty plugin instances.
    """

    def __init__(
        self,
        default_mapping: Mapping[
            str, PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]
        ],
        mapping: Mapping[
            str, PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]
        ],
    ):
        super().__init__()
        self._default_mapping = default_mapping
        self._mapping: MutableMapping[
            str, PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]
        ] = {
            **default_mapping,
            **mapping,
        }

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        self._mapping = {
            **self._default_mapping,
            **assert_mapping(self._load_item, _assert_gramps_type)(dump),
        }

    def _load_item(
        self, dump: Dump
    ) -> PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]:
        configuration = PluginInstanceConfiguration[
            _ClassedPluginDefinitionT, _PluginT
        ]("-")
        configuration.load(dump)
        return configuration

    @override
    def dump(self) -> Dump:
        return {
            gramps_type: configuration.dump()
            for gramps_type, configuration in self._mapping.items()
        }

    def __getitem__(
        self, gramps_type: str
    ) -> PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]:
        return self._mapping[gramps_type]

    def __setitem__(
        self,
        gramps_type: str,
        configuration: PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT],
    ) -> None:
        self.assert_mutable()
        self._mapping[gramps_type] = configuration

    def __delitem__(self, gramps_type: str) -> None:
        self.assert_mutable()
        del self._mapping[gramps_type]

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)


class FamilyTreeConfiguration(Configuration):
    """
    Configure a single Gramps family tree.
    """

    def __init__(
        self,
        source: Path | str,
        *,
        event_types: Mapping[
            str,
            PluginInstanceConfiguration[ClassedPluginDefinition[EventType], EventType],
        ]
        | None = None,
        place_types: Mapping[
            str,
            PluginInstanceConfiguration[ClassedPluginDefinition[PlaceType], PlaceType],
        ]
        | None = None,
        presence_roles: Mapping[
            str,
            PluginInstanceConfiguration[
                ClassedPluginDefinition[PresenceRole], PresenceRole
            ],
        ]
        | None = None,
    ):
        super().__init__()
        self._source = source
        self._event_types = PluginMapping[
            ClassedPluginDefinition[EventType], EventType
        ](
            {
                gramps_value: PluginInstanceConfiguration(event_type)
                for gramps_value, event_type in DEFAULT_EVENT_TYPES_MAPPING.items()
            },
            event_types or {},
        )
        self._place_types = PluginMapping[
            ClassedPluginDefinition[PlaceType], PlaceType
        ](
            {
                gramps_value: PluginInstanceConfiguration(event_type)
                for gramps_value, event_type in DEFAULT_PLACE_TYPES_MAPPING.items()
            },
            place_types or {},
        )
        self._presence_roles = PluginMapping[
            ClassedPluginDefinition[PresenceRole], PresenceRole
        ](
            {
                gramps_value: PluginInstanceConfiguration(event_type)
                for gramps_value, event_type in DEFAULT_PRESENCE_ROLES_MAPPING.items()
            },
            presence_roles or {},
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
    def event_types(
        self,
    ) -> PluginMapping[ClassedPluginDefinition[EventType], EventType]:
        """
        How to map event types.
        """
        return self._event_types

    @property
    def place_types(
        self,
    ) -> PluginMapping[ClassedPluginDefinition[PlaceType], PlaceType]:
        """
        How to map place types.
        """
        return self._place_types

    @property
    def presence_roles(
        self,
    ) -> PluginMapping[ClassedPluginDefinition[PresenceRole], PresenceRole]:
        """
        How to map presence roles.
        """
        return self._presence_roles

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
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
        assert_record(
            OptionalField("file", assert_path() | assert_setattr(self, "source")),
            OptionalField("name", assert_str() | assert_setattr(self, "source")),
            OptionalField("event_types", self.event_types.load),
            OptionalField("place_types", self.place_types.load),
            OptionalField("presence_roles", self.presence_roles.load),
        )(dump)

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
    def _load_item(self, dump: Dump) -> FamilyTreeConfiguration:
        # Use a dummy path to satisfy initializer arguments.
        # It will be overridden when loading the dump.
        item = FamilyTreeConfiguration(Path())
        item.load(dump)
        return item


class GrampsConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
    """

    def __init__(
        self,
        *,
        family_trees: Iterable[FamilyTreeConfiguration] | None = None,
        executable: Path | None = None,
    ):
        super().__init__()
        self._family_trees = FamilyTreeConfigurationSequence(family_trees)
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
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        assert_record(
            OptionalField("family_trees", self.family_trees.load),
            OptionalField(
                "executable", assert_path() | assert_setattr(self, "executable")
            ),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump: DumpMapping[Dump] = {"family_trees": self.family_trees.dump()}
        if self.executable is not None:
            dump["executable"] = str(self.executable)
        return dump
