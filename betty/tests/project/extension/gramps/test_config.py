from collections.abc import Mapping
from pathlib import Path

import pytest
from typing_extensions import override

from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.place_type.place_types import Borough
from betty.ancestry.presence_role.presence_roles import Attendee
from betty.exception import HumanFacingException
from betty.gramps.loader import (
    DEFAULT_EVENT_TYPES_MAPPING,
    DEFAULT_PLACE_TYPES_MAPPING,
    DEFAULT_PRESENCE_ROLES_MAPPING,
)
from betty.plugin.config import PluginInstanceConfiguration
from betty.project.extension.gramps.config import (
    FamilyTreeConfiguration,
    FamilyTreeConfigurationSequence,
    GrampsConfiguration,
    PluginMapping,
)
from betty.serde.dump import Dump
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBaseNewSut,
    ConfigurationCollectionTestBaseSutConfigurations,
)
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.exception import raises_error
from betty.test_utils.plugin.classed import (
    ClassedDummyPlugin,
    ClassedDummyPluginDefinition,
)


class TestFamilyTreeConfigurationSequence(
    ConfigurationSequenceTestBase[FamilyTreeConfiguration]
):
    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[FamilyTreeConfiguration, int]:
        return FamilyTreeConfigurationSequence

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[FamilyTreeConfiguration]:
        return (
            FamilyTreeConfiguration(Path() / "gramps-1"),
            FamilyTreeConfiguration(Path() / "gramps-2"),
            FamilyTreeConfiguration(Path() / "gramps-3"),
            FamilyTreeConfiguration(Path() / "gramps-4"),
        )


class TestFamilyTreeConfiguration:
    def test___init____with_source_file_path(self, tmp_path: Path) -> None:
        file_path = tmp_path / "betty.gramps"
        sut = FamilyTreeConfiguration(file_path)
        assert sut.source == file_path

    def test___init____with_source_name(self) -> None:
        name = "my-first-family-tree"
        sut = FamilyTreeConfiguration(name)
        assert sut.source == name

    def test___init____with_event_types(self, tmp_path: Path) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            tmp_path, event_types={gramps_type: PluginInstanceConfiguration(plugin_id)}
        )
        assert sut.event_types[gramps_type].id == plugin_id
        assert sut.event_types["Birth"].id == Birth.plugin.id

    def test___init____with_place_types(self, tmp_path: Path) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            tmp_path, place_types={gramps_type: PluginInstanceConfiguration(plugin_id)}
        )
        assert sut.place_types[gramps_type].id == plugin_id
        assert sut.place_types["Borough"].id == Borough.plugin.id

    def test___init____with_presence_roles(self, tmp_path: Path) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            tmp_path,
            presence_roles={gramps_type: PluginInstanceConfiguration(plugin_id)},
        )
        assert sut.presence_roles[gramps_type].id == plugin_id
        assert sut.presence_roles["Aide"].id == Attendee.plugin.id

    def test_source(self) -> None:
        source = "my-first-family-tree"
        sut = FamilyTreeConfiguration(source)
        assert sut.source == source

    def test_event_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert sut.event_types.dump() == {
            gramps_type: plugin.id
            for gramps_type, plugin in DEFAULT_EVENT_TYPES_MAPPING.items()
        }

    def test_place_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert sut.place_types.dump() == {
            gramps_type: plugin.id
            for gramps_type, plugin in DEFAULT_PLACE_TYPES_MAPPING.items()
        }

    def test_presence_roles(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert sut.presence_roles.dump() == {
            gramps_type: plugin.id
            for gramps_type, plugin in DEFAULT_PRESENCE_ROLES_MAPPING.items()
        }

    async def test_load__with_minimal_configuration(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {"file": str(file_path)}
        FamilyTreeConfiguration(tmp_path).load(dump)

    async def test_load__with_event_types(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "file": str(file_path),
            "event_types": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }
        sut = FamilyTreeConfiguration(tmp_path)
        sut.load(dump)
        assert sut.event_types["my-first-gramps-type"].id == "my-first-betty-plugin-id"
        assert sut.event_types["Birth"].id == Birth.plugin.id

    async def test_load__with_place_types(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "file": str(file_path),
            "place_types": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }
        sut = FamilyTreeConfiguration(tmp_path)
        sut.load(dump)
        assert sut.place_types["my-first-gramps-type"].id == "my-first-betty-plugin-id"
        assert sut.place_types["Borough"].id == Borough.plugin.id

    async def test_load__with_presence_roles(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "file": str(file_path),
            "presence_roles": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }
        sut = FamilyTreeConfiguration(tmp_path)
        sut.load(dump)
        assert (
            sut.presence_roles["my-first-gramps-type"].id == "my-first-betty-plugin-id"
        )
        assert sut.presence_roles["Aide"].id == Attendee.plugin.id

    async def test_load__without_dict_should_error(self, tmp_path: Path) -> None:
        dump = None
        with raises_error(error_type=HumanFacingException):
            FamilyTreeConfiguration(tmp_path).load(dump)

    async def test_dump__with_minimal_configuration(self, tmp_path: Path) -> None:
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

    async def test_dump__with_event_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(
            tmp_path,
            event_types={
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        actual = sut.dump()["event_types"]
        assert isinstance(actual, Mapping)
        assert actual["my-first-gramps-type"] == "my-first-betty-plugin-id"

    async def test_dump__with_place_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(
            tmp_path,
            place_types={
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        actual = sut.dump()["place_types"]
        assert isinstance(actual, Mapping)
        assert actual["my-first-gramps-type"] == "my-first-betty-plugin-id"

    async def test_dump__with_presence_roles(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(
            tmp_path,
            presence_roles={
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        actual = sut.dump()["presence_roles"]
        assert isinstance(actual, Mapping)
        assert actual["my-first-gramps-type"] == "my-first-betty-plugin-id"

    def test_get_mutables(self) -> None:
        sut = FamilyTreeConfiguration(Path(__file__))
        sut.immutable = True
        assert sut.event_types.immutable
        assert sut.place_types.immutable
        assert sut.presence_roles.immutable


class TestPluginMapping:
    def test___init____with_values(self) -> None:
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin](
            {
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "some-elses-betty-plugin-id"
                )
            },
            {
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                ),
                "my-second-gramps-type": PluginInstanceConfiguration(
                    "my-second-betty-plugin-id"
                ),
            },
        )
        assert sut["my-first-gramps-type"].id == "my-first-betty-plugin-id"
        assert sut["my-second-gramps-type"].id == "my-second-betty-plugin-id"

    def test_load__without_values(self) -> None:
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin]({}, {})
        sut.load({})
        assert sut.dump() == {}

    def test_load__with_values(self) -> None:
        dump: Dump = {
            "my-first-gramps-type": "my-first-betty-plugin-id",
            "my-second-gramps-type": "my-second-betty-plugin-id",
        }
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin](
            {
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "some-elses-betty-plugin-id"
                )
            },
            {},
        )
        sut.load(dump)
        assert sut.dump() == dump
        assert sut["my-first-gramps-type"].id == "my-first-betty-plugin-id"
        assert sut["my-second-gramps-type"].id == "my-second-betty-plugin-id"

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
    def test_load__should_error(self, dump: Dump) -> None:
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin]({}, {})
        with pytest.raises(HumanFacingException):
            sut.load(dump)

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {},
                PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin]({}, {}),
            ),
            (
                {"my-first-gramps-type": "my-first-betty-plugin-id"},
                PluginMapping(
                    {},
                    {
                        "my-first-gramps-type": PluginInstanceConfiguration(
                            "my-first-betty-plugin-id"
                        )
                    },
                ),
            ),
        ],
    )
    def test_dump(
        self,
        expected: Dump,
        sut: PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin],
    ) -> None:
        assert sut.dump() == expected

    def test___getitem__(self) -> None:
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin](
            {},
            {
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        assert sut["my-first-gramps-type"].id == "my-first-betty-plugin-id"

    def test___setitem__(self) -> None:
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin]({}, {})
        sut["my-first-gramps-type"] = PluginInstanceConfiguration(
            "my-first-betty-plugin-id"
        )
        assert sut["my-first-gramps-type"].id == "my-first-betty-plugin-id"

    def test___delitem__(self) -> None:
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin](
            {},
            {
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        del sut["my-first-gramps-type"]
        with pytest.raises(KeyError):
            sut["my-first-gramps-type"]

    def test___iter____without_items(self) -> None:
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin]({}, {})
        assert list(iter(sut)) == []

    def test___iter____with_items(self) -> None:
        sut = PluginMapping[ClassedDummyPluginDefinition, ClassedDummyPlugin](
            {},
            {
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        assert list(iter(sut)) == ["my-first-gramps-type"]


class TestGrampsConfiguration:
    async def test___init____with_family_trees(self) -> None:
        family_trees = [FamilyTreeConfiguration("my-first-family-tree")]
        sut = GrampsConfiguration(family_trees=family_trees)
        assert list(sut.family_trees) == family_trees

    async def test___init____with_executable(self) -> None:
        executable = Path("my-first-gramps")
        sut = GrampsConfiguration(executable=executable)
        assert sut.executable == executable

    async def test_family_trees(self) -> None:
        family_trees = [FamilyTreeConfiguration("my-first-family-tree")]
        sut = GrampsConfiguration()
        sut.family_trees = family_trees  # type: ignore[assignment]
        assert list(sut.family_trees) == family_trees

    async def test_executable(self) -> None:
        executable = Path("my-first-gramps")
        sut = GrampsConfiguration()
        sut.executable = executable
        assert sut.executable == executable

    async def test_load__with_minimal_configuration(self) -> None:
        dump: Dump = {}
        GrampsConfiguration().load(dump)

    async def test_load__without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=HumanFacingException):
            GrampsConfiguration().load(dump)

    async def test_load__with_family_tree(self) -> None:
        family_tree_name = "my-first-family-tree"
        dump: Dump = {
            "family_trees": [
                {
                    "name": family_tree_name,
                },
            ],
        }
        sut = GrampsConfiguration()
        sut.load(dump)
        assert sut.family_trees[0].source == family_tree_name

    async def test_dump__with_minimal_configuration(self) -> None:
        sut = GrampsConfiguration()
        assert sut.dump() == {"family_trees": []}

    async def test_dump__with_family_tree(self, tmp_path: Path) -> None:
        family_tree_name = "my-first-family-tree"
        sut = GrampsConfiguration()
        sut.family_trees.append(FamilyTreeConfiguration(family_tree_name))
        actual = sut.dump()
        actual["family_trees"][0].pop("event_types")  # type: ignore[arg-type, index, union-attr]
        actual["family_trees"][0].pop("place_types")  # type: ignore[arg-type, index, union-attr]
        actual["family_trees"][0].pop("presence_roles")  # type: ignore[arg-type, index, union-attr]
        expected = {
            "family_trees": [
                {
                    "name": family_tree_name,
                },
            ],
        }
        assert actual == expected

    def test_get_mutables(self) -> None:
        sut = GrampsConfiguration()
        sut.immutable = True
        assert sut.family_trees.immutable
