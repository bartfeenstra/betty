"""
Provide configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Self, final, TYPE_CHECKING, TypeVar

from typing_extensions import override

from betty.ancestry.event_type.event_types import (
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
from betty.ancestry.gender.genders import Female, Male, Unknown as UnknownGender
from betty.ancestry.place_type.place_types import (
    Borough,
    Building,
    City,
    Country,
    County,
    Department,
    District,
    Farm,
    Hamlet,
    Locality,
    Municipality,
    Neighborhood,
    Number,
    Parish,
    Province,
    Region,
    State,
    Street,
    Town,
    Unknown as UnknownPlaceType,
    Village,
)
from betty.ancestry.presence_role.presence_roles import (
    Celebrant,
    Subject,
    Unknown as UnknownPresenceRole,
    Witness,
    Attendee,
    Informant,
)
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
from betty.typing import internal

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping
    from collections.abc import Mapping, MutableMapping, Iterable


_PluginT = TypeVar("_PluginT", bound=Plugin)

DEFAULT_EVENT_TYPE_MAP: Mapping[str, MachineName] = {
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
DEFAULT_PLACE_TYPE_MAP: Mapping[str, MachineName] = {
    "Borough": Borough.plugin_id(),
    "Building": Building.plugin_id(),
    "City": City.plugin_id(),
    "Country": Country.plugin_id(),
    "County": County.plugin_id(),
    "Department": Department.plugin_id(),
    "District": District.plugin_id(),
    "Farm": Farm.plugin_id(),
    "Hamlet": Hamlet.plugin_id(),
    "Locality": Locality.plugin_id(),
    "Municipality": Municipality.plugin_id(),
    "Neighborhood": Neighborhood.plugin_id(),
    "Number": Number.plugin_id(),
    "Parish": Parish.plugin_id(),
    "Province": Province.plugin_id(),
    "Region": Region.plugin_id(),
    "State": State.plugin_id(),
    "Street": Street.plugin_id(),
    "Town": Town.plugin_id(),
    "Unknown": UnknownPlaceType.plugin_id(),
    "Village": Village.plugin_id(),
}

DEFAULT_PRESENCE_ROLE_MAP: Mapping[str, MachineName] = {
    "Aide": Attendee.plugin_id(),
    "Bride": Subject.plugin_id(),
    "Celebrant": Celebrant.plugin_id(),
    "Clergy": Celebrant.plugin_id(),
    "Family": Subject.plugin_id(),
    "Groom": Subject.plugin_id(),
    "Informant": Informant.plugin_id(),
    "Primary": Subject.plugin_id(),
    "Unknown": UnknownPresenceRole.plugin_id(),
    "Witness": Witness.plugin_id(),
}
DEFAULT_GENDER_MAP: Mapping[str, MachineName] = {
    "F": Female.plugin_id(),
    "M": Male.plugin_id(),
    "U": UnknownGender.plugin_id(),
}


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
    def dump(self) -> Dump:
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
        event_types: Mapping[str, MachineName] | None = None,
        place_types: Mapping[str, MachineName] | None = None,
        presence_roles: Mapping[str, MachineName] | None = None,
        genders: Mapping[str, MachineName] | None = None,
    ):
        super().__init__()
        self.file_path = file_path
        self._event_types = PluginMapping(
            {**DEFAULT_EVENT_TYPE_MAP, **(event_types or {})}
        )
        self._genders = PluginMapping({**DEFAULT_GENDER_MAP, **(genders or {})})
        self._place_types = PluginMapping(
            {**DEFAULT_PLACE_TYPE_MAP, **(place_types or {})}
        )
        self._presence_roles = PluginMapping(
            {**DEFAULT_PRESENCE_ROLE_MAP, **(presence_roles or {})}
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
    def genders(self) -> PluginMapping:
        """
        How to map genders.
        """
        return self._genders

    @property
    def place_types(self) -> PluginMapping:
        """
        How to map place types.
        """
        return self._place_types

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
            OptionalField("genders", self.genders.load),
            OptionalField("place_types", self.place_types.load),
            OptionalField("presence_roles", self.presence_roles.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "file": str(self.file_path) if self.file_path else None,
            "event_types": self.event_types.dump(),
            "genders": self.genders.dump(),
            "place_types": self.place_types.dump(),
            "presence_roles": self.presence_roles.dump(),
        }

    @override
    def update(self, other: Self) -> None:
        self.file_path = other.file_path
        self.event_types.update(other.event_types)
        self.genders.update(other.genders)
        self.place_types.update(other.place_types)
        self.presence_roles.update(other.presence_roles)


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
    Provide configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
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
    def dump(self) -> DumpMapping[Dump]:
        return {"family_trees": self.family_trees.dump()}
