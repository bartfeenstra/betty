"""
Provide configuration for the :py:class:`betty.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Self, final, TYPE_CHECKING, TypeVar

from typing_extensions import override

from betty.ancestry.event_type import (
    Adoption,
    Baptism,
    Birth,
    Burial,
    Confirmation,
    Cremation,
    Death,
    Divorce,
    DivorceAnnouncement,
    Emigration,
    Engagement,
    Immigration,
    Marriage,
    MarriageAnnouncement,
    Occupation,
    Residence,
    Retirement,
    Will,
)
from betty.ancestry.presence_role import Celebrant, Subject, Attendee, Witness
from betty.assertion import (
    RequiredField,
    OptionalField,
    assert_record,
    assert_path,
    assert_setattr,
    assert_mapping,
    assert_len,
    assert_str,
)
from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.machine_name import assert_machine_name, MachineName
from betty.plugin import PluginRepository, Plugin
from betty.serde.dump import minimize, Dump, DumpMapping
from betty.typing import internal, Void, Voidable

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping, Iterable


_PluginT = TypeVar("_PluginT", bound=Plugin)


def _assert_gramps_type(value: Any) -> str:
    event_type = assert_str()(value)
    assert_len(minimum=1)(event_type)
    return event_type


@internal
@final
class PluginMapping(Configuration):
    """
    Map Gramps types to Betty plugin IDs.
    """

    def __init__(self, mapping: Mapping[str, MachineName] | None = None):
        super().__init__()
        self._mapping: MutableMapping[str, MachineName] = {
            **self._default_mapping(),
            **(mapping or {}),
        }

    async def to_plugins(
        self, plugins: PluginRepository[_PluginT]
    ) -> Mapping[str, type[_PluginT]]:
        """
        Hydrate the mapping into plugins.
        """
        return {
            gramps_type: await plugins.get(plugin_id)
            for gramps_type, plugin_id in self._mapping.items()
        }

    @override
    def load(self, dump: Dump) -> None:
        self._mapping = assert_mapping(assert_machine_name(), _assert_gramps_type)(dump)

    @override
    def dump(self) -> Voidable[Dump]:
        if not self._mapping:
            return Void
        # Dumps are mutable, so return a new dict which may then be changed without impacting ``self``.
        return dict(self._mapping)

    @override
    def update(self, other: Self) -> None:
        self._mapping = dict(other._mapping)

    def _default_mapping(self) -> Mapping[str, MachineName]:
        return {}

    def __getitem__(self, gramps_type: str) -> MachineName:
        return self._mapping[gramps_type]

    def __setitem__(self, gramps_type: str, plugin_id: MachineName) -> None:
        self._mapping[gramps_type] = plugin_id

    def __delitem__(self, gramps_type: str) -> None:
        del self._mapping[gramps_type]


class FamilyTreeConfiguration(Configuration):
    """
    Configure a single Gramps family tree.
    """

    def __init__(
        self,
        file_path: Path,
        *,
        event_types: PluginMapping | None = None,
        presence_roles: PluginMapping | None = None,
    ):
        super().__init__()
        self.file_path = file_path
        self._event_types = event_types or PluginMapping(
            {
                "Adopted": Adoption.plugin_id(),
                "Baptism": Baptism.plugin_id(),
                "Birth": Birth.plugin_id(),
                "Burial": Burial.plugin_id(),
                "Confirmation": Confirmation.plugin_id(),
                "Cremation": Cremation.plugin_id(),
                "Death": Death.plugin_id(),
                "Divorce": Divorce.plugin_id(),
                "Divorce Filing": DivorceAnnouncement.plugin_id(),
                "Emigration": Emigration.plugin_id(),
                "Engagement": Engagement.plugin_id(),
                "Immigration": Immigration.plugin_id(),
                "Marriage": Marriage.plugin_id(),
                "Marriage Banns": MarriageAnnouncement.plugin_id(),
                "Occupation": Occupation.plugin_id(),
                "Residence": Residence.plugin_id(),
                "Retirement": Retirement.plugin_id(),
                "Will": Will.plugin_id(),
            }
        )
        self._presence_roles = presence_roles or PluginMapping(
            {
                "Celebrant": Celebrant.plugin_id(),
                "Bride": Subject.plugin_id(),
                "Family": Subject.plugin_id(),
                "Groom": Subject.plugin_id(),
                "Primary": Subject.plugin_id(),
                "Unknown": Attendee.plugin_id(),
                "Witness": Witness.plugin_id(),
            }
        )

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FamilyTreeConfiguration):
            return False
        return self._file_path == other.file_path

    @property
    def file_path(self) -> Path | None:
        """
        The path to the Gramps family tree file.
        """
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: Path | None) -> None:
        self._file_path = file_path

    @property
    def event_types(self) -> PluginMapping:
        """
        How to map event types.
        """
        return self._event_types

    @property
    def presence_roles(self) -> PluginMapping:
        """
        How to map presence roles.
        """
        return self._presence_roles

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("file", assert_path() | assert_setattr(self, "file_path")),
            OptionalField("event_types", self.event_types.load),
            OptionalField("presence_roles", self.presence_roles.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return minimize(
            {
                "file": str(self.file_path) if self.file_path else None,
                "event_types": self.event_types.dump(),
                "presence_roles": self.presence_roles.dump(),
            }
        )

    @override
    def update(self, other: Self) -> None:
        self.file_path = other.file_path


class FamilyTreeConfigurationSequence(ConfigurationSequence[FamilyTreeConfiguration]):
    """
    Configure zero or more Gramps family trees.
    """

    @override
    def load_item(self, dump: Dump) -> FamilyTreeConfiguration:
        # Use a dummy path to satisfy initializer arguments.
        # It will be overridden when loading the fump.
        item = FamilyTreeConfiguration(Path())
        item.load(dump)
        return item


class GrampsConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.extension.gramps.Gramps` extension.
    """

    def __init__(
        self, *, family_trees: Iterable[FamilyTreeConfiguration] | None = None
    ):
        super().__init__()
        self._family_trees = FamilyTreeConfigurationSequence(family_trees)

    @property
    def family_trees(self) -> FamilyTreeConfigurationSequence:
        """
        The Gramps family trees to load.
        """
        return self._family_trees

    @override
    def update(self, other: Self) -> None:
        self._family_trees.update(other._family_trees)

    @override
    def load(self, dump: Dump) -> None:
        assert_record(OptionalField("family_trees", self.family_trees.load))(dump)

    @override
    def dump(self) -> Voidable[DumpMapping[Dump]]:
        return minimize({"family_trees": self.family_trees.dump()}, True)
