"""
Provide configuration for the :py:class:`betty.extension.gramps.Gramps` extension.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any, Self

from typing_extensions import override

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
from betty.config.collections.mapping import ConfigurationMapping
from betty.config.collections.sequence import ConfigurationSequence
from betty.machine_name import assert_machine_name, MachineName
from betty.serde.dump import minimize, Dump, VoidableDump


def _assert_gramps_event_type(value: Any) -> str:
    event_type = assert_str()(value)
    assert_len(minimum=1)(event_type)
    return event_type


class FamilyTreeEventTypeConfiguration(Configuration):
    """
    Configure for loading Gramps events.
    """

    _gramps_event_type: str
    _event_type_id: MachineName

    def __init__(self, gramps_event_type: str, event_type_id: MachineName):
        super().__init__()
        self.gramps_event_type = gramps_event_type
        self.event_type_id = event_type_id

    @property
    def gramps_event_type(self) -> str:
        """
        The Gramps event type this configuration applies to.
        """
        return self._gramps_event_type

    @gramps_event_type.setter
    def gramps_event_type(self, event_type: str) -> None:
        self._gramps_event_type = _assert_gramps_event_type(event_type)

    @property
    def event_type_id(self) -> MachineName:
        """
        The ID of the Betty event type to load Gramps events of type :py:attr:`betty.extension.gramps.config.FamilyTreeEventTypeConfiguration.gramps_event_type` as.
        """
        return self._event_type_id

    @event_type_id.setter
    def event_type_id(self, event_type_id: MachineName) -> None:
        self._event_type_id = assert_machine_name()(event_type_id)

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField(
                "gramps_event_type", assert_setattr(self, "gramps_event_type")
            ),
            RequiredField("event_type", assert_setattr(self, "event_type_id")),
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return {
            "gramps_event_type": self.gramps_event_type,
            "event_type": self.event_type_id,
        }

    @override
    def update(self, other: Self) -> None:
        self.gramps_event_type = other.gramps_event_type
        self.event_type_id = other.event_type_id


class FamilyTreeEventTypeConfigurationMapping(
    ConfigurationMapping[str, FamilyTreeEventTypeConfiguration]
):
    """
    Configure how to map Gramps events to Betty events.
    """

    def __init__(
        self, configurations: Iterable[FamilyTreeEventTypeConfiguration] | None = None
    ):
        if configurations is None:
            configurations = [
                FamilyTreeEventTypeConfiguration("Adopted", "adoption"),
                FamilyTreeEventTypeConfiguration("Baptism", "baptism"),
                FamilyTreeEventTypeConfiguration("Birth", "birth"),
                FamilyTreeEventTypeConfiguration("Burial", "burial"),
                FamilyTreeEventTypeConfiguration("Confirmation", "confirmation"),
                FamilyTreeEventTypeConfiguration("Cremation", "cremation"),
                FamilyTreeEventTypeConfiguration("Death", "death"),
                FamilyTreeEventTypeConfiguration("Divorce", "divorce"),
                FamilyTreeEventTypeConfiguration(
                    "Divorce Filing", "divorce-announcement"
                ),
                FamilyTreeEventTypeConfiguration("Emigration", "emigration"),
                FamilyTreeEventTypeConfiguration("Engagement", "engagement"),
                FamilyTreeEventTypeConfiguration("Immigration", "immigration"),
                FamilyTreeEventTypeConfiguration("Marriage", "marriage"),
                FamilyTreeEventTypeConfiguration(
                    "Marriage Banns", "marriage-announcement"
                ),
                FamilyTreeEventTypeConfiguration("Occupation", "occupation"),
                FamilyTreeEventTypeConfiguration("Residence", "residence"),
                FamilyTreeEventTypeConfiguration("Retirement", "retirement"),
                FamilyTreeEventTypeConfiguration("Will", "will"),
            ]
        super().__init__(configurations)

    @override
    def _minimize_item_dump(self) -> bool:
        return True

    @override
    def _get_key(self, configuration: FamilyTreeEventTypeConfiguration) -> str:
        return configuration.gramps_event_type

    @override
    def _load_key(self, item_dump: Dump, key_dump: str) -> Dump:
        mapping_dump = assert_mapping()(item_dump)
        mapping_dump["gramps_event_type"] = _assert_gramps_event_type(key_dump)
        return mapping_dump

    @override
    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        mapping_dump = assert_mapping()(item_dump)
        return mapping_dump, mapping_dump.pop("entity_type")

    @override
    def load_item(self, dump: Dump) -> FamilyTreeEventTypeConfiguration:
        # Use dummy configuration for now to satisfy the initializer.
        # It will be overridden when loading the dump.
        configuration = FamilyTreeEventTypeConfiguration("-", "-")
        configuration.load(dump)
        return configuration


class FamilyTreeConfiguration(Configuration):
    """
    Configure a single Gramps family tree.
    """

    def __init__(
        self,
        file_path: Path,
        *,
        event_types: Iterable[FamilyTreeEventTypeConfiguration] | None = None,
    ):
        super().__init__()
        self.file_path = file_path
        self._event_types = FamilyTreeEventTypeConfigurationMapping(event_types)

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
    def event_types(self) -> FamilyTreeEventTypeConfigurationMapping:
        """
        How to map event types.
        """
        return self._event_types

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("file", assert_path() | assert_setattr(self, "file_path"))
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return {"file": str(self.file_path) if self.file_path else None}

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
    def dump(self) -> VoidableDump:
        return minimize({"family_trees": self.family_trees.dump()}, True)
