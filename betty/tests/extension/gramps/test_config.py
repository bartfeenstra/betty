from pathlib import Path
from typing import Any

from betty.extension.gramps.config import FamilyTreeConfiguration, GrampsConfiguration
from betty.serde.dump import Void, Dump
from betty.serde.load import AssertionFailed
from betty.tests.serde import raises_error


class TestFamilyTreeConfiguration:
    async def test_load_with_minimal_configuration(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: dict[str, Any] = {"file": str(file_path)}
        FamilyTreeConfiguration().load(dump)

    async def test_load_without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            FamilyTreeConfiguration().load(dump)

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = FamilyTreeConfiguration()
        expected = {
            "file": None,
        }
        assert expected == sut.dump()

    async def test_dump_with_file_path(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = FamilyTreeConfiguration()
        sut.file_path = file_path
        expected = {
            "file": str(file_path),
        }
        assert expected == sut.dump()

    async def test_update(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = FamilyTreeConfiguration()
        other = FamilyTreeConfiguration()
        other.file_path = file_path
        sut.update(other)
        assert sut.file_path == file_path

    async def test___eq___is_equal(self) -> None:
        sut = FamilyTreeConfiguration()
        other = FamilyTreeConfiguration()
        assert sut == other

    async def test___eq___is_not_equal_type(self) -> None:
        sut = FamilyTreeConfiguration()
        assert sut != 123

    async def test___eq___is_not_equal(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration()
        sut.file_path = tmp_path / "ancestry.gramps"
        other = FamilyTreeConfiguration()
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
        sut = GrampsConfiguration.load(dump)
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
