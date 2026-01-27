from pathlib import Path

from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.place_type.place_types import Borough
from betty.ancestry.presence_role.presence_roles import Attendee
from betty.plugin.config import PluginConfiguration
from betty.project.extension.gramps.config import (
    FamilyTreeConfiguration,
    GrampsConfiguration,
)
from betty.test_utils.data import DataTestBase


class TestFamilyTreeConfiguration(DataTestBase[FamilyTreeConfiguration]):
    sut_cls = FamilyTreeConfiguration

    def test___init____with_file(self) -> None:
        file = Path()
        sut = FamilyTreeConfiguration(file=file)
        assert sut.source == file

    def test___init____with_name(self) -> None:
        name = "my-first-family-tree"
        sut = FamilyTreeConfiguration(name=name)
        assert sut.source == name

    def test___init____with_event_types(self) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            name="my-first-family-tree",
            event_types={gramps_type: PluginConfiguration(plugin_id)},
        )
        assert sut.event_types[gramps_type].id == plugin_id
        assert sut.event_types["Birth"].id == Birth.plugin().id

    def test___init____with_place_types(self) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            name="my-first-family-tree",
            place_types={gramps_type: PluginConfiguration(plugin_id)},
        )
        assert sut.place_types[gramps_type].id == plugin_id
        assert sut.place_types["Borough"].id == Borough.plugin().id

    def test___init____with_presence_roles(self) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTreeConfiguration(
            name="my-first-family-tree",
            presence_roles={gramps_type: PluginConfiguration(plugin_id)},
        )
        assert sut.presence_roles[gramps_type].id == plugin_id
        assert sut.presence_roles["Aide"].id == Attendee.plugin().id

    def test_source(self) -> None:
        name = "my-first-family-tree"
        sut = FamilyTreeConfiguration(name=name)
        assert sut.source == name


class TestGrampsConfiguration(DataTestBase[GrampsConfiguration]):
    sut_cls = GrampsConfiguration

    async def test___init____with_family_trees(self) -> None:
        family_tree = FamilyTreeConfiguration(name="my-first-family-tree")
        sut = GrampsConfiguration(family_trees=[family_tree])
        assert sut.family_trees == [family_tree]

    async def test___init____with_executable(self) -> None:
        executable = Path("my-first-gramps")
        sut = GrampsConfiguration(executable=executable)
        assert sut.executable == executable

    async def test_family_trees(self) -> None:
        family_trees = [FamilyTreeConfiguration(name="my-first-family-tree")]
        sut = GrampsConfiguration()
        sut.family_trees = family_trees
        assert list(sut.family_trees) == family_trees

    async def test_executable(self) -> None:
        executable = Path("my-first-gramps")
        sut = GrampsConfiguration()
        sut.executable = executable
        assert sut.executable == executable
