import gzip
from pathlib import Path
from tempfile import TemporaryDirectory

from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.note import Note
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.event_type import EventTypeManufacturer
from betty.event_types.birth import Birth
from betty.gramps import machinify
from betty.load import LoaderManufacturer, load
from betty.loaders.gramps import FamilyTree, Gramps, GrampsData
from betty.place_type import PlaceTypeManufacturer
from betty.place_types.borough import Borough
from betty.place_types.city import City
from betty.role import RoleManufacturer
from betty.roles.attendee import Attendee
from betty.roles.subject import Subject
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.data import DataTestBase


class TestGramps:
    async def test_load__with_event_type_mapping(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        family_tree_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
    <header>
        <created date="2019-03-09" version="4.2.8"/>
        <researcher>
        </researcher>
    </header>
    <events>
        <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
            <type>Birth</type>
            <dateval val="0000-00-00" quality="calculated"/>
        </event>
    </events>
</database>
""".strip()
        gramps_family_tree_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_family_tree_path, "w") as f:
            f.write(family_tree_xml.encode("utf-8"))

        async with isolated_project_factory(
            loaders=[
                LoaderManufacturer(
                    Gramps.plugin(),
                    GrampsData(
                        family_trees=[
                            FamilyTree(
                                gramps_family_tree_path,
                                event_types={"Birth": EventTypeManufacturer("birth")},
                            )
                        ]
                    ),
                )
            ],
        ) as project:
            await load(project)
            assert isinstance(
                project.ancestry[Event][machinify("E0000")].event_type, Birth
            )

    async def test_load__with_place_type_mapping(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        family_tree_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
    <header>
        <created date="2019-03-09" version="4.2.8"/>
        <researcher>
        </researcher>
    </header>
    <places>
        <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0001" type="City">
        </placeobj>
    </places>
</database>
""".strip()
        gramps_family_tree_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_family_tree_path, "w") as f:
            f.write(family_tree_xml.encode("utf-8"))

        async with isolated_project_factory(
            loaders=[
                LoaderManufacturer(
                    Gramps.plugin(),
                    GrampsData(
                        family_trees=[
                            FamilyTree(
                                gramps_family_tree_path,
                                place_types={"City": PlaceTypeManufacturer("city")},
                            )
                        ]
                    ),
                )
            ],
        ) as project:
            await load(project)
            assert isinstance(
                project.ancestry[Place][machinify("P0001")].place_type, City
            )

    async def test_load__with_role_map(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        family_tree_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
    <header>
        <created date="2019-03-09" version="4.2.8"/>
        <researcher>
        </researcher>
    </header>
    <people>
        <person handle="_e1dd3c1caf863ee0081cc2cc16f" change="1552131917" id="I0000">
            <gender>U</gender>
            <eventref hlink="_e7692ea23775e80643fe4fcf91" role="MyFirstRole"/>
        </person>
    </people>
    <events>
        <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
            <type>Birth</type>
            <dateval val="0000-00-00" quality="calculated"/>
        </event>
    </events>
</database>
""".strip()
        gramps_family_tree_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_family_tree_path, "w") as f:
            f.write(family_tree_xml.encode("utf-8"))

        async with isolated_project_factory(
            loaders=[
                LoaderManufacturer(
                    Gramps.plugin(),
                    GrampsData(
                        family_trees=[
                            FamilyTree(
                                gramps_family_tree_path,
                                roles={"MyFirstRole": RoleManufacturer("subject")},
                            )
                        ]
                    ),
                )
            ],
        ) as project:
            await load(project)
            assert isinstance(
                next(iter(project.ancestry[Person][machinify("I0000")].presences)).role,
                Subject,
            )

    async def test_load__with_multiple_family_trees(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        family_tree_one_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
  <header>
    <created date="2019-03-09" version="4.2.8"/>
    <researcher>
    </researcher>
  </header>
  <people>
    <person handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="I0001">
        <gender>U</gender>
    </person>
  </people>
  <places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0001" type="Unknown">
    </placeobj>
  </places>
  <events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0001">
      <type>Birth</type>
    </event>
  </events>
  <sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0001">
      <stitle>A Whisper</stitle>
      <reporef hlink="_e2c257f50fd27b1c841d7497448" medium="Book"/>
    </source>
  </sources>
  <repositories>
    <repository handle="_e2c257f50fd27b1c841d7497448" change="1558277216" id="R0001">
      <rname>Library of Alexandria</rname>
    </repository>
  </repositories>
  <citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0001">
      <sourceref hlink="_e2b5e77b4cc5c91c9ed60a6cb39"/>
    </citation>
  </citations>
  <notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0001" type="Transcript">
      <text></text>
    </note>
  </notes>
</database>
""".strip()
        family_tree_two_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
  <header>
    <created date="2019-03-09" version="4.2.8"/>
    <researcher>
    </researcher>
  </header>
  <people>
    <person handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="I0002">
        <gender>U</gender>
    </person>
  </people>
  <places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0002" type="Unknown">
    </placeobj>
  </places>
  <events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0002">
      <type>Birth</type>
    </event>
  </events>
  <sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0002">
      <stitle>A Whisper</stitle>
      <reporef hlink="_e2c257f50fd27b1c841d7497448" medium="Book"/>
    </source>
  </sources>
  <repositories>
    <repository handle="_e2c257f50fd27b1c841d7497448" change="1558277216" id="R0002">
      <rname>Library of Alexandria</rname>
    </repository>
  </repositories>
  <citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0002">
      <sourceref hlink="_e2b5e77b4cc5c91c9ed60a6cb39"/>
    </citation>
  </citations>
  <notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0002" type="Transcript">
      <text></text>
    </note>
  </notes>
</database>
""".strip()
        with TemporaryDirectory() as working_directory_str:
            working_directory = Path(working_directory_str)
            gramps_family_tree_one = working_directory / "one.gramps"
            with gzip.open(gramps_family_tree_one, "w") as f:
                f.write(family_tree_one_xml.encode("utf-8"))

            gramps_family_tree_two = working_directory / "two.gramps"
            with gzip.open(gramps_family_tree_two, "w") as f:
                f.write(family_tree_two_xml.encode("utf-8"))

            async with isolated_project_factory(
                loaders=[
                    LoaderManufacturer(
                        Gramps.plugin(),
                        GrampsData(
                            family_trees=[
                                FamilyTree(gramps_family_tree_one),
                                FamilyTree(gramps_family_tree_two),
                            ]
                        ),
                    )
                ],
            ) as project:
                await load(project)
                assert machinify("I0001") in project.ancestry[Person]
                assert machinify("I0002") in project.ancestry[Person]
                assert machinify("P0001") in project.ancestry[Place]
                assert machinify("P0002") in project.ancestry[Place]
                assert machinify("E0001") in project.ancestry[Event]
                assert machinify("E0002") in project.ancestry[Event]
                assert machinify("S0001") in project.ancestry[Source]
                assert machinify("S0002") in project.ancestry[Source]
                assert machinify("R0001") in project.ancestry[Source]
                assert machinify("R0002") in project.ancestry[Source]
                assert machinify("C0001") in project.ancestry[Citation]
                assert machinify("C0002") in project.ancestry[Citation]
                assert machinify("N0001") in project.ancestry[Note]
                assert machinify("N0002") in project.ancestry[Note]


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


class TestGrampsData(DataTestBase[GrampsData]):
    sut_cls = GrampsData

    async def test___init____with_family_trees(self) -> None:
        family_tree = FamilyTree(name="my-first-family-tree")
        sut = GrampsData(family_trees=[family_tree])
        assert sut.family_trees == [family_tree]

    async def test___init____with_executable(self) -> None:
        executable = Path("my-first-gramps")
        sut = GrampsData(executable=executable)
        assert sut.executable is executable

    async def test_family_trees(self) -> None:
        family_trees = [FamilyTree(name="my-first-family-tree")]
        sut = GrampsData()
        sut.family_trees = family_trees
        assert list(sut.family_trees) == family_trees

    async def test_executable(self) -> None:
        executable = Path("my-first-gramps")
        sut = GrampsData()
        sut.executable = executable
        assert sut.executable is executable
