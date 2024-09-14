from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from typing_extensions import override

import pytest

from betty.assertion.error import AssertionFailed
from betty.extension.gramps.config import (
    FamilyTreeConfiguration,
    GrampsConfiguration,
    FamilyTreeConfigurationSequence,
    FamilyTreeEventTypeConfiguration,
    FamilyTreeEventTypeConfigurationMapping,
)
from betty.serde.dump import Dump
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.typing import Void


class TestFamilyTreeConfigurationSequence(
    ConfigurationSequenceTestBase[FamilyTreeConfiguration]
):
    def get_sut(
        self, configurations: Iterable[FamilyTreeConfiguration] | None = None
    ) -> FamilyTreeConfigurationSequence:
        return FamilyTreeConfigurationSequence(configurations)

    def get_configurations(
        self,
    ) -> tuple[
        FamilyTreeConfiguration,
        FamilyTreeConfiguration,
        FamilyTreeConfiguration,
        FamilyTreeConfiguration,
    ]:
        return (
            FamilyTreeConfiguration(Path() / "gramps-1"),
            FamilyTreeConfiguration(Path() / "gramps-2"),
            FamilyTreeConfiguration(Path() / "gramps-3"),
            FamilyTreeConfiguration(Path() / "gramps-4"),
        )


class TestFamilyTreeConfiguration:
    def test_event_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert len(sut.event_types)

    async def test_load_with_minimal_configuration(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Mapping[str, Any] = {"file": str(file_path)}
        FamilyTreeConfiguration(tmp_path).load(dump)

    async def test_load_without_dict_should_error(self, tmp_path: Path) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            FamilyTreeConfiguration(tmp_path).load(dump)

    async def test_dump_with_minimal_configuration(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        expected = {
            "file": str(tmp_path),
        }
        assert sut.dump() == expected

    async def test_dump_with_file_path(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = FamilyTreeConfiguration(tmp_path)
        sut.file_path = file_path
        expected = {
            "file": str(file_path),
        }
        assert sut.dump() == expected

    async def test_update(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = FamilyTreeConfiguration(tmp_path)
        other = FamilyTreeConfiguration(tmp_path)
        other.file_path = file_path
        sut.update(other)
        assert sut.file_path == file_path

    async def test___eq___is_equal(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        other = FamilyTreeConfiguration(tmp_path)
        assert sut == other

    async def test___eq___is_not_equal_type(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert sut != 123

    async def test___eq___is_not_equal(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        sut.file_path = tmp_path / "ancestry.gramps"
        other = FamilyTreeConfiguration(tmp_path)
        assert sut != other


class TestFamilyTreeEventTypeConfiguration:
    async def test_gramps_event_type(self) -> None:
        gramps_event_type = "my-first-gramps-event-type"
        sut = FamilyTreeEventTypeConfiguration(
            gramps_event_type, "my-first-betty-event-type"
        )
        assert sut.gramps_event_type == gramps_event_type

    async def test_event_type_id(self) -> None:
        event_type_id = "my-first-betty-event-type"
        sut = FamilyTreeEventTypeConfiguration(
            "my-first-gramps-event-type", event_type_id
        )
        assert sut.event_type_id == event_type_id

    async def test_load(self) -> None:
        gramps_event_type = "my-first-gramps-event-type"
        event_type_id = "my-first-betty-event-type"
        dump: Dump = {
            "gramps_event_type": gramps_event_type,
            "event_type": event_type_id,
        }
        sut = FamilyTreeEventTypeConfiguration("-", "-")
        sut.load(dump)
        assert sut.gramps_event_type == gramps_event_type
        assert sut.event_type_id == event_type_id

    @pytest.mark.parametrize(
        "dump",
        [
            {},
            {"gramps_event_type": "-"},
            {"event_type": "-"},
        ],
    )
    async def test_load_with_invalid_dump_should_error(self, dump: Dump) -> None:
        sut = FamilyTreeEventTypeConfiguration("-", "-")
        with pytest.raises(AssertionFailed):
            sut.load(dump)

    async def test_dump(self) -> None:
        gramps_event_type = "my-first-gramps-event-type"
        event_type_id = "my-first-betty-event-type"
        sut = FamilyTreeEventTypeConfiguration(gramps_event_type, event_type_id)
        dump = sut.dump()
        assert dump == {
            "gramps_event_type": gramps_event_type,
            "event_type": event_type_id,
        }

    async def test_update(self) -> None:
        gramps_event_type = "my-first-gramps-event-type"
        event_type_id = "my-first-betty-event-type"
        other = FamilyTreeEventTypeConfiguration(gramps_event_type, event_type_id)
        sut = FamilyTreeEventTypeConfiguration("-", "-")
        sut.update(other)
        assert sut.gramps_event_type == gramps_event_type
        assert sut.event_type_id == event_type_id


class TestFamilyTreeEventTypeConfigurationMapping(
    ConfigurationMappingTestBase[str, FamilyTreeEventTypeConfiguration]
):
    @override
    def get_configuration_keys(
        self,
    ) -> tuple[str, str, str, str]:
        return "gramps-foo", "gramps-bar", "gramps-baz", "gramps-qux"

    @override
    def get_configurations(
        self,
    ) -> tuple[
        FamilyTreeEventTypeConfiguration,
        FamilyTreeEventTypeConfiguration,
        FamilyTreeEventTypeConfiguration,
        FamilyTreeEventTypeConfiguration,
    ]:
        return (
            FamilyTreeEventTypeConfiguration("gramps-foo", "betty-foo"),
            FamilyTreeEventTypeConfiguration("gramps-bar", "betty-bar"),
            FamilyTreeEventTypeConfiguration("gramps-baz", "betty-baz"),
            FamilyTreeEventTypeConfiguration("gramps-qux", "betty-qux"),
        )

    @override
    def get_sut(
        self, configurations: Iterable[FamilyTreeEventTypeConfiguration] | None = None
    ) -> FamilyTreeEventTypeConfigurationMapping:
        return FamilyTreeEventTypeConfigurationMapping(configurations)


class TestGrampsConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        GrampsConfiguration().load(dump)

    async def test_load_without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            GrampsConfiguration().load(dump)

    async def test_load_with_family_tree(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "family_trees": [
                {
                    "file": str(file_path),
                },
            ],
        }
        sut = GrampsConfiguration()
        sut.load(dump)
        assert sut.family_trees[0].file_path == file_path

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = GrampsConfiguration()
        assert sut.dump() is Void

    async def test_dump_with_family_tree(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = GrampsConfiguration()
        sut.family_trees.append(FamilyTreeConfiguration(file_path=file_path))
        expected = {
            "family_trees": [
                {
                    "file": str(file_path),
                },
            ],
        }
        assert sut.dump() == expected

    async def test_update(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = GrampsConfiguration()
        other = GrampsConfiguration()
        other.family_trees.append(FamilyTreeConfiguration(file_path=file_path))
        sut.update(other)
        assert sut.family_trees[0].file_path == file_path
