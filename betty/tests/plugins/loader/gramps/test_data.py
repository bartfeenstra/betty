from pathlib import Path

from betty.event_type import EventTypeManufacturer
from betty.place_type import PlaceTypeManufacturer
from betty.plugins.event_type.birth import Birth
from betty.plugins.loader.gramps import (
    FamilyTree,
    GrampsConfiguration,
)
from betty.plugins.place_type.borough import Borough
from betty.plugins.role.attendee import Attendee
from betty.role import RoleManufacturer
from betty.test_utils.data import DataTestBase


class TestFamilyTree(DataTestBase[FamilyTree]):
    sut_cls = FamilyTree

    def test___init____with_file(self) -> None:
        file = Path()
        sut = FamilyTree(file=file)
        assert sut.source == file

    def test___init____with_name(self) -> None:
        name = "my-first-family-tree"
        sut = FamilyTree(name=name)
        assert sut.source == name

    def test___init____with_event_types(self) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTree(
            name="my-first-family-tree",
            event_types={gramps_type: EventTypeManufacturer(plugin_id)},
        )
        assert sut.event_types[gramps_type].plugin_id == plugin_id
        assert sut.event_types["Birth"].plugin_id == Birth.plugin().id

    def test___init____with_place_types(self) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTree(
            name="my-first-family-tree",
            place_types={gramps_type: PlaceTypeManufacturer(plugin_id)},
        )
        assert sut.place_types[gramps_type].plugin_id == plugin_id
        assert sut.place_types["Borough"].plugin_id == Borough.plugin().id

    def test___init____with_roles(self) -> None:
        gramps_type = "my-first-gramps-type"
        plugin_id = "my-first-betty-plugin-id"
        sut = FamilyTree(
            name="my-first-family-tree",
            roles={gramps_type: RoleManufacturer(plugin_id)},
        )
        assert sut.roles[gramps_type].plugin_id == plugin_id
        assert sut.roles["Aide"].plugin_id == Attendee.plugin().id

    def test_source(self) -> None:
        name = "my-first-family-tree"
        sut = FamilyTree(name=name)
        assert sut.source == name


class TestGrampsConfiguration(DataTestBase[GrampsConfiguration]):
    sut_cls = GrampsConfiguration

    async def test___init____with_family_trees(self) -> None:
        family_tree = FamilyTree(name="my-first-family-tree")
        sut = GrampsConfiguration(family_trees=[family_tree])
        assert sut.family_trees == [family_tree]

    async def test___init____with_executable(self) -> None:
        executable = Path("my-first-gramps")
        sut = GrampsConfiguration(executable=executable)
        assert sut.executable == executable

    async def test_family_trees(self) -> None:
        family_trees = [FamilyTree(name="my-first-family-tree")]
        sut = GrampsConfiguration()
        sut.family_trees = family_trees
        assert list(sut.family_trees) == family_trees

    async def test_executable(self) -> None:
        executable = Path("my-first-gramps")
        sut = GrampsConfiguration()
        sut.executable = executable
        assert sut.executable == executable
