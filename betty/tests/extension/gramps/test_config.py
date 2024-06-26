from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from betty.extension.gramps.config import (
    FamilyTreeConfiguration,
    GrampsConfiguration,
    FamilyTreeConfigurationSequence,
)
from betty.serde.dump import Void, Dump
from betty.serde.load import AssertionFailed
from betty.tests.serde import raises_error
from betty.tests.test_config import ConfigurationSequenceTestBase


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

    async def test_load_item(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        dumps = [configuration.dump() for configuration in configurations]
        non_void_dumps: Sequence[Dump] = [
            dump  # type: ignore[misc]
            for dump in dumps
            if dump is not Void
        ]
        assert non_void_dumps, "At least one configuration object must return a configuration dump that is not Void"
        for dump in non_void_dumps:
            sut.load_item(dump)


class TestFamilyTreeConfiguration:
    async def test_load_with_minimal_configuration(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: dict[str, Any] = {"file": str(file_path)}
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
        assert expected == sut.dump()

    async def test_dump_with_file_path(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = FamilyTreeConfiguration(tmp_path)
        sut.file_path = file_path
        expected = {
            "file": str(file_path),
        }
        assert expected == sut.dump()

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


class TestGrampsConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: dict[str, Any] = {}
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
        assert expected == sut.dump()

    async def test_update(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = GrampsConfiguration()
        other = GrampsConfiguration()
        other.family_trees.append(FamilyTreeConfiguration(file_path=file_path))
        sut.update(other)
        assert sut.family_trees[0].file_path == file_path
