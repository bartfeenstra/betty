"""
Provide configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, final, TYPE_CHECKING, TypeVar

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
    BarMitzvah,
    BatMitzvah,
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
from betty.plugin import Plugin
from betty.plugin.config import PluginInstanceConfiguration
from betty.typing import internal

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping
    from collections.abc import Mapping, MutableMapping, Iterable, Iterator

_PluginT = TypeVar("_PluginT", bound=Plugin)


DEFAULT_EVENT_TYPE_MAP: Mapping[str, PluginInstanceConfiguration] = {
    "Adopted": PluginInstanceConfiguration(Adoption),
    "Adult Christening": PluginInstanceConfiguration(Baptism),
    "Baptism": PluginInstanceConfiguration(Baptism),
    "Bar Mitzvah": PluginInstanceConfiguration(BarMitzvah),
    "Bat Mitzvah": PluginInstanceConfiguration(BatMitzvah),
    "Birth": PluginInstanceConfiguration(Birth),
    "Burial": PluginInstanceConfiguration(Burial),
    "Christening": PluginInstanceConfiguration(Baptism),
    "Confirmation": PluginInstanceConfiguration(Confirmation),
    "Cremation": PluginInstanceConfiguration(Cremation),
    "Death": PluginInstanceConfiguration(Death),
    "Divorce": PluginInstanceConfiguration(Divorce),
    "Divorce Filing": PluginInstanceConfiguration(DivorceAnnouncement),
    "Emigration": PluginInstanceConfiguration(Emigration),
    "Engagement": PluginInstanceConfiguration(Engagement),
    "Immigration": PluginInstanceConfiguration(Immigration),
    "Marriage": PluginInstanceConfiguration(Marriage),
    "Marriage Banns": PluginInstanceConfiguration(MarriageAnnouncement),
    "Occupation": PluginInstanceConfiguration(Occupation),
    "Residence": PluginInstanceConfiguration(Residence),
    "Retirement": PluginInstanceConfiguration(Retirement),
    "Will": PluginInstanceConfiguration(Will),
}


DEFAULT_PLACE_TYPE_MAP: Mapping[str, PluginInstanceConfiguration] = {
    "Borough": PluginInstanceConfiguration(Borough),
    "Building": PluginInstanceConfiguration(Building),
    "City": PluginInstanceConfiguration(City),
    "Country": PluginInstanceConfiguration(Country),
    "County": PluginInstanceConfiguration(County),
    "Department": PluginInstanceConfiguration(Department),
    "District": PluginInstanceConfiguration(District),
    "Farm": PluginInstanceConfiguration(Farm),
    "Hamlet": PluginInstanceConfiguration(Hamlet),
    "Locality": PluginInstanceConfiguration(Locality),
    "Municipality": PluginInstanceConfiguration(Municipality),
    "Neighborhood": PluginInstanceConfiguration(Neighborhood),
    "Number": PluginInstanceConfiguration(Number),
    "Parish": PluginInstanceConfiguration(Parish),
    "Province": PluginInstanceConfiguration(Province),
    "Region": PluginInstanceConfiguration(Region),
    "State": PluginInstanceConfiguration(State),
    "Street": PluginInstanceConfiguration(Street),
    "Town": PluginInstanceConfiguration(Town),
    "Unknown": PluginInstanceConfiguration(UnknownPlaceType),
    "Village": PluginInstanceConfiguration(Village),
}


DEFAULT_PRESENCE_ROLE_MAP: Mapping[str, PluginInstanceConfiguration] = {
    "Aide": PluginInstanceConfiguration(Attendee),
    "Bride": PluginInstanceConfiguration(Subject),
    "Celebrant": PluginInstanceConfiguration(Celebrant),
    "Clergy": PluginInstanceConfiguration(Celebrant),
    "Family": PluginInstanceConfiguration(Subject),
    "Groom": PluginInstanceConfiguration(Subject),
    "Informant": PluginInstanceConfiguration(Informant),
    "Primary": PluginInstanceConfiguration(Subject),
    "Unknown": PluginInstanceConfiguration(UnknownPresenceRole),
    "Witness": PluginInstanceConfiguration(Witness),
}


DEFAULT_GENDER_MAP: Mapping[str, PluginInstanceConfiguration] = {
    "F": PluginInstanceConfiguration(Female),
    "M": PluginInstanceConfiguration(Male),
    "U": PluginInstanceConfiguration(UnknownGender),
}


def _assert_gramps_type(value: Any) -> str:
    event_type = assert_str()(value)
    assert_len(minimum=1)(event_type)
    return event_type


@internal
@final
class PluginMapping(Configuration):
    """
    Map Gramps types to Betty plugin instances.
    """

    def __init__(
        self,
        default_mapping: Mapping[str, PluginInstanceConfiguration],
        mapping: Mapping[str, PluginInstanceConfiguration],
    ):
        super().__init__()
        self._default_mapping = default_mapping
        self._mapping: MutableMapping[str, PluginInstanceConfiguration] = {
            **default_mapping,
            **mapping,
        }

    @override
    def load(self, dump: Dump) -> None:
        self._mapping = {
            **self._default_mapping,
            **assert_mapping(self._load_item, _assert_gramps_type)(dump),
        }

    def _load_item(self, dump: Dump) -> PluginInstanceConfiguration:
        configuration = PluginInstanceConfiguration("-")
        configuration.load(dump)
        return configuration

    @override
    def dump(self) -> Dump:
        return {
            gramps_type: configuration.dump()
            for gramps_type, configuration in self._mapping.items()
        }

    def __getitem__(self, gramps_type: str) -> PluginInstanceConfiguration:
        return self._mapping[gramps_type]

    def __setitem__(
        self, gramps_type: str, configuration: PluginInstanceConfiguration
    ) -> None:
        self._mapping[gramps_type] = configuration

    def __delitem__(self, gramps_type: str) -> None:
        del self._mapping[gramps_type]

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)


class FamilyTreeConfiguration(Configuration):
    """
    Configure a single Gramps family tree.
    """

    def __init__(
        self,
        file_path: Path,
        *,
        event_types: Mapping[str, PluginInstanceConfiguration] | None = None,
        place_types: Mapping[str, PluginInstanceConfiguration] | None = None,
        presence_roles: Mapping[str, PluginInstanceConfiguration] | None = None,
        genders: Mapping[str, PluginInstanceConfiguration] | None = None,
    ):
        super().__init__()
        self.file_path = file_path
        self._event_types = PluginMapping(DEFAULT_EVENT_TYPE_MAP, event_types or {})
        self._genders = PluginMapping(DEFAULT_GENDER_MAP, genders or {})
        self._place_types = PluginMapping(DEFAULT_PLACE_TYPE_MAP, place_types or {})
        self._presence_roles = PluginMapping(
            DEFAULT_PRESENCE_ROLE_MAP, presence_roles or {}
        )

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


class FamilyTreeConfigurationSequence(ConfigurationSequence[FamilyTreeConfiguration]):
    """
    Configure zero or more Gramps family trees.
    """

    @override
    def load_item(self, dump: Dump) -> FamilyTreeConfiguration:
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
    def load(self, dump: Dump) -> None:
        assert_record(OptionalField("family_trees", self.family_trees.load))(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {"family_trees": self.family_trees.dump()}
