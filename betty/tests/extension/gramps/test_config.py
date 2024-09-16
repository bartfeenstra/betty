from collections.abc import Iterable
from pathlib import Path

import pytest
from typing_extensions import override

from betty.assertion.error import AssertionFailed
from betty.extension.gramps.config import (
    FamilyTreeConfiguration,
    GrampsConfiguration,
    FamilyTreeConfigurationSequence,
    PluginMapping,
)
from betty.machine_name import MachineName
from betty.plugin import PluginNotFound, Plugin
from betty.plugin.static import StaticPluginRepository
from betty.serde.dump import Dump
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.plugin import DummyPlugin
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
        sut.event_types  # noqa B018

    def test_place_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        sut.place_types  # noqa B018

    def test_presence_roles(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        sut.presence_roles  # noqa B018

    async def test_load_with_minimal_configuration(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {"file": str(file_path)}
        FamilyTreeConfiguration(tmp_path).load(dump)

    async def test_load_with_event_types(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "file": str(file_path),
            "event_types": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }
        sut = FamilyTreeConfiguration(tmp_path)
        sut.load(dump)
        assert sut.event_types["my-first-gramps-type"] == "my-first-betty-plugin-id"

    async def test_load_with_place_types(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "file": str(file_path),
            "place_types": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }
        sut = FamilyTreeConfiguration(tmp_path)
        sut.load(dump)
        assert sut.place_types["my-first-gramps-type"] == "my-first-betty-plugin-id"

    async def test_load_with_presence_roles(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "file": str(file_path),
            "presence_roles": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }
        sut = FamilyTreeConfiguration(tmp_path)
        sut.load(dump)
        assert sut.presence_roles["my-first-gramps-type"] == "my-first-betty-plugin-id"

    async def test_load_without_dict_should_error(self, tmp_path: Path) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            FamilyTreeConfiguration(tmp_path).load(dump)

    async def test_dump_with_minimal_configuration(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        actual = sut.dump()
        assert len(
            actual.pop("event_types")  # type: ignore[arg-type]
        )
        assert len(
            actual.pop("place_types")  # type: ignore[arg-type]
        )
        assert len(
            actual.pop("presence_roles")  # type: ignore[arg-type]
        )
        assert actual == {
            "file": str(tmp_path),
        }

    async def test_dump_with_event_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(
            tmp_path,
            event_types=PluginMapping(
                {"my-first-gramps-type": "my-first-betty-plugin-id"}
            ),
            place_types=PluginMapping(),
            presence_roles=PluginMapping(),
        )
        assert sut.dump() == {
            "file": str(tmp_path),
            "event_types": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }

    async def test_dump_with_place_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(
            tmp_path,
            place_types=PluginMapping(
                {"my-first-gramps-type": "my-first-betty-plugin-id"}
            ),
            event_types=PluginMapping(),
            presence_roles=PluginMapping(),
        )
        assert sut.dump() == {
            "file": str(tmp_path),
            "place_types": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }

    async def test_dump_with_presence_roles(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(
            tmp_path,
            presence_roles=PluginMapping(
                {"my-first-gramps-type": "my-first-betty-plugin-id"}
            ),
            event_types=PluginMapping(),
            place_types=PluginMapping(),
        )
        assert sut.dump() == {
            "file": str(tmp_path),
            "presence_roles": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }

    async def test_update(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = FamilyTreeConfiguration(tmp_path)
        # @todo Add plugin mappings!
        other = FamilyTreeConfiguration(tmp_path)
        other.file_path = file_path
        sut.update(other)
        assert sut.file_path == file_path

    # @todo UGH err remove __eq__ altogether?
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


class TestPluginMapping:
    def test_load_without_values(self) -> None:
        sut = PluginMapping()
        sut.load({})
        assert sut.dump() is Void

    def test_load_with_values(self) -> None:
        dump: Dump = {"my-first-gramps-type": "my-first-betty-plugin-id"}
        sut = PluginMapping()
        sut.load(dump)
        assert sut.dump() == dump
        assert sut["my-first-gramps-type"] == "my-first-betty-plugin-id"

    @pytest.mark.parametrize(
        "dump",
        [
            True,
            False,
            None,
            "abc",
            123,
            [],
        ],
    )
    def test_load_should_error(self, dump: Dump) -> None:
        sut = PluginMapping()
        with pytest.raises(AssertionFailed):
            sut.load(dump)

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (Void, PluginMapping()),
            (
                {"my-first-gramps-type": "my-first-betty-plugin-id"},
                PluginMapping({"my-first-gramps-type": "my-first-betty-plugin-id"}),
            ),
        ],
    )
    def test_dump(self, expected: Dump, sut: PluginMapping) -> None:
        assert sut.dump() == expected

    def test_update(self) -> None:
        sut = PluginMapping()
        other = PluginMapping({"my-first-gramps-type": "my-first-betty-plugin-id"})
        sut.update(other)
        assert sut["my-first-gramps-type"] == "my-first-betty-plugin-id"

    def test___getitem__(self) -> None:
        sut = PluginMapping({"my-first-gramps-type": "my-first-betty-plugin-id"})
        assert sut["my-first-gramps-type"] == "my-first-betty-plugin-id"

    def test___setitem__(self) -> None:
        sut = PluginMapping()
        sut["my-first-gramps-type"] = "my-first-betty-plugin-id"
        assert sut["my-first-gramps-type"] == "my-first-betty-plugin-id"

    def test___delitem__(self) -> None:
        sut = PluginMapping({"my-first-gramps-type": "my-first-betty-plugin-id"})
        del sut["my-first-gramps-type"]
        with pytest.raises(KeyError):
            sut["my-first-gramps-type"]

    async def test_to_plugins_without_values(self) -> None:
        sut = PluginMapping()
        actual = await sut.to_plugins(StaticPluginRepository[Plugin]())
        assert actual == {}

    async def test_to_plugins_with_values(self) -> None:
        class _Plugin(DummyPlugin):
            @override
            @classmethod
            def plugin_id(cls) -> MachineName:
                return "my-first-betty-plugin-id"

        sut = PluginMapping({"my-first-gramps-type": "my-first-betty-plugin-id"})
        actual = await sut.to_plugins(StaticPluginRepository(_Plugin))
        assert actual == {"my-first-gramps-type": _Plugin}

    async def test_to_plugins_should_error(self) -> None:
        sut = PluginMapping({"my-first-gramps-type": "my-first-betty-plugin-id"})
        with pytest.raises(PluginNotFound):
            await sut.to_plugins(StaticPluginRepository())


class TestGrampsConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: Dump = {}
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
        actual = sut.dump()
        actual["family_trees"][0].pop("event_types")  # type: ignore[arg-type, index, union-attr]
        actual["family_trees"][0].pop("place_types")  # type: ignore[arg-type, index, union-attr]
        actual["family_trees"][0].pop("presence_roles")  # type: ignore[arg-type, index, union-attr]
        expected = {
            "family_trees": [
                {
                    "file": str(file_path),
                },
            ],
        }
        assert actual == expected

    async def test_update(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = GrampsConfiguration()
        other = GrampsConfiguration()
        other.family_trees.append(FamilyTreeConfiguration(file_path=file_path))
        sut.update(other)
        assert sut.family_trees[0].file_path == file_path
