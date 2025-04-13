"""
Provide configuration for the :py:class:`betty.project.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar, final
from warnings import warn

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_len,
    assert_mapping,
    assert_path,
    assert_record,
    assert_setattr,
    assert_str,
)
from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.gramps.loader import (
    DEFAULT_EVENT_TYPES_MAPPING,
    DEFAULT_PLACE_TYPES_MAPPING,
    DEFAULT_PRESENCE_ROLES_MAPPING,
)
from betty.plugin import Plugin
from betty.plugin.config import PluginInstanceConfiguration
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, MutableMapping

    from betty.mutability import Mutable
    from betty.serde.dump import Dump, DumpMapping

_PluginT = TypeVar("_PluginT", bound=Plugin)


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
        self.assert_mutable()
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

    The ``genders`` argument has been deprecated since Betty 0.4.13. There is no alternative.
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
        self._event_types = PluginMapping(
            {
                gramps_value: PluginInstanceConfiguration(event_type)
                for gramps_value, event_type in DEFAULT_EVENT_TYPES_MAPPING.items()
            },
            event_types or {},
        )
        if genders is not None:
            warn(
                "The ``genders`` argument has been deprecated since Betty 0.4.13. There is no alternative.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        self._genders = PluginMapping({}, genders or {})
        self._place_types = PluginMapping(
            {
                gramps_value: PluginInstanceConfiguration(event_type)
                for gramps_value, event_type in DEFAULT_PLACE_TYPES_MAPPING.items()
            },
            place_types or {},
        )
        self._presence_roles = PluginMapping(
            {
                gramps_value: PluginInstanceConfiguration(event_type)
                for gramps_value, event_type in DEFAULT_PRESENCE_ROLES_MAPPING.items()
            },
            presence_roles or {},
        )

    @override
    def get_mutable_instances(self) -> Iterable[Mutable]:
        return (
            self._event_types,
            self._genders,
            self._place_types,
            self._presence_roles,
        )

    @property
    def file_path(self) -> Path | None:
        """
        The path to the Gramps family tree file.
        """
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: Path | None) -> None:
        self.assert_mutable()
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
        self.assert_mutable()
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
        self, *, family_trees: Iterable[FamilyTreeConfiguration] | None = None
    ):
        super().__init__()
        self._family_trees = FamilyTreeConfigurationSequence(family_trees)

    @override
    def get_mutable_instances(self) -> Iterable[Mutable]:
        return (self._family_trees,)

    @property
    def family_trees(self) -> FamilyTreeConfigurationSequence:
        """
        The Gramps family trees to load.
        """
        return self._family_trees

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        assert_record(OptionalField("family_trees", self.family_trees.load))(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {"family_trees": self.family_trees.dump()}
