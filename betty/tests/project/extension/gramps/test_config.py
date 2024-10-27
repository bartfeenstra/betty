from collections.abc import Iterable, Mapping
from pathlib import Path

import pytest

from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.gender.genders import Female
from betty.ancestry.place_type.place_types import Borough
from betty.ancestry.presence_role.presence_roles import Attendee
from betty.assertion.error import AssertionFailed
from betty.plugin.config import PluginInstanceConfiguration
from betty.project.extension.gramps.config import (
    FamilyTreeConfiguration,
    GrampsConfiguration,
    FamilyTreeConfigurationSequence,
    PluginMapping,
    DEFAULT_EVENT_TYPE_MAP,
    DEFAULT_GENDER_MAP,
    DEFAULT_PLACE_TYPE_MAP,
    DEFAULT_PRESENCE_ROLE_MAP,
)
from betty.serde.dump import Dump
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase


class TestFamilyTreeConfigurationSequence(
    ConfigurationSequenceTestBase[FamilyTreeConfiguration]
):
    async def get_sut(
        self, configurations: Iterable[FamilyTreeConfiguration] | None = None
    ) -> FamilyTreeConfigurationSequence:
        return FamilyTreeConfigurationSequence(configurations)

    async def get_configurations(
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
    def test___init___with_event_types(self, tmp_path: Path) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            tmp_path, event_types={gramps_type: PluginInstanceConfiguration(plugin_id)}
        )
        assert sut.event_types[gramps_type].id == plugin_id
        assert sut.event_types["Birth"].id == Birth.plugin_id()

    def test___init___with_genders(self, tmp_path: Path) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            tmp_path, genders={gramps_type: PluginInstanceConfiguration(plugin_id)}
        )
        assert sut.genders[gramps_type].id == plugin_id
        assert sut.genders["F"].id == Female.plugin_id()

    def test___init___with_place_types(self, tmp_path: Path) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            tmp_path, place_types={gramps_type: PluginInstanceConfiguration(plugin_id)}
        )
        assert sut.place_types[gramps_type].id == plugin_id
        assert sut.place_types["Borough"].id == Borough.plugin_id()

    def test___init___with_presence_roles(self, tmp_path: Path) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            tmp_path,
            presence_roles={gramps_type: PluginInstanceConfiguration(plugin_id)},
        )
        assert sut.presence_roles[gramps_type].id == plugin_id
        assert sut.presence_roles["Aide"].id == Attendee.plugin_id()

    def test_event_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert sut.event_types.dump() == {
            gramps_type: configuration.dump()
            for gramps_type, configuration in DEFAULT_EVENT_TYPE_MAP.items()
        }

    def test_genders(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert sut.genders.dump() == {
            gramps_type: configuration.dump()
            for gramps_type, configuration in DEFAULT_GENDER_MAP.items()
        }

    def test_place_types(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert sut.place_types.dump() == {
            gramps_type: configuration.dump()
            for gramps_type, configuration in DEFAULT_PLACE_TYPE_MAP.items()
        }

    def test_presence_roles(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(tmp_path)
        assert sut.presence_roles.dump() == {
            gramps_type: configuration.dump()
            for gramps_type, configuration in DEFAULT_PRESENCE_ROLE_MAP.items()
        }

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
        assert sut.event_types["my-first-gramps-type"].id == "my-first-betty-plugin-id"
        assert sut.event_types["Birth"].id == Birth.plugin_id()

    async def test_load_with_genders(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "file": str(file_path),
            "genders": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }
        sut = FamilyTreeConfiguration(tmp_path)
        sut.load(dump)
        assert sut.genders["my-first-gramps-type"].id == "my-first-betty-plugin-id"
        assert sut.genders["F"].id == Female.plugin_id()

    async def test_load_with_place_types(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        dump: Dump = {
            "file": str(file_path),
            "place_types": {"my-first-gramps-type": "my-first-betty-plugin-id"},
        }
        sut = FamilyTreeConfiguration(tmp_path)
        sut.load(dump)
        assert sut.place_types["my-first-gramps-type"].id == "my-first-betty-plugin-id"
        assert sut.place_types["Borough"].id == Borough.plugin_id()

    async def test_load_with_presence_roles(self, tmp_path: Path) -> None:
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
        assert sut.presence_roles["Aide"].id == Attendee.plugin_id()

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
            actual.pop("genders")  # type: ignore[arg-type]
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
            event_types={
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        actual = sut.dump()["event_types"]
        assert isinstance(actual, Mapping)
        assert actual["my-first-gramps-type"] == "my-first-betty-plugin-id"

    async def test_dump_with_genders(self, tmp_path: Path) -> None:
        sut = FamilyTreeConfiguration(
            tmp_path,
            genders={
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        actual = sut.dump()["genders"]
        assert isinstance(actual, Mapping)
        assert actual["my-first-gramps-type"] == "my-first-betty-plugin-id"

    async def test_dump_with_place_types(self, tmp_path: Path) -> None:
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

    async def test_dump_with_presence_roles(self, tmp_path: Path) -> None:
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


class TestPluginMapping:
    def test___init___with_values(self) -> None:
        sut = PluginMapping(
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

    def test_load_without_values(self) -> None:
        sut = PluginMapping({}, {})
        sut.load({})
        assert sut.dump() == {}

    def test_load_with_values(self) -> None:
        dump: Dump = {
            "my-first-gramps-type": "my-first-betty-plugin-id",
            "my-second-gramps-type": "my-second-betty-plugin-id",
        }
        sut = PluginMapping(
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
    def test_load_should_error(self, dump: Dump) -> None:
        sut = PluginMapping({}, {})
        with pytest.raises(AssertionFailed):
            sut.load(dump)

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            ({}, PluginMapping({}, {})),
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
    def test_dump(self, expected: Dump, sut: PluginMapping) -> None:
        assert sut.dump() == expected

    def test___getitem__(self) -> None:
        sut = PluginMapping(
            {},
            {
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        assert sut["my-first-gramps-type"].id == "my-first-betty-plugin-id"

    def test___setitem__(self) -> None:
        sut = PluginMapping({}, {})
        sut["my-first-gramps-type"] = PluginInstanceConfiguration(
            "my-first-betty-plugin-id"
        )
        assert sut["my-first-gramps-type"].id == "my-first-betty-plugin-id"

    def test___delitem__(self) -> None:
        sut = PluginMapping(
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

    def test___iter___without_items(self) -> None:
        sut = PluginMapping({}, {})
        assert list(iter(sut)) == []

    def test___iter___with_items(self) -> None:
        sut = PluginMapping(
            {},
            {
                "my-first-gramps-type": PluginInstanceConfiguration(
                    "my-first-betty-plugin-id"
                )
            },
        )
        assert list(iter(sut)) == ["my-first-gramps-type"]


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
        assert sut.dump() == {"family_trees": []}

    async def test_dump_with_family_tree(self, tmp_path: Path) -> None:
        file_path = tmp_path / "ancestry.gramps"
        sut = GrampsConfiguration()
        sut.family_trees.append(FamilyTreeConfiguration(file_path=file_path))
        actual = sut.dump()
        actual["family_trees"][0].pop("event_types")  # type: ignore[arg-type, index, union-attr]
        actual["family_trees"][0].pop("genders")  # type: ignore[arg-type, index, union-attr]
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
