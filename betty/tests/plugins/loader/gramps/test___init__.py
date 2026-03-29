import gzip
from pathlib import Path

from aiofiles.tempfile import TemporaryDirectory

from betty.event_type import EventTypeManufacturer
from betty.load import LoaderManufacturer, load
from betty.place_type import PlaceTypeManufacturer
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.event import Event
from betty.plugins.entity.note import Note
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.source import Source
from betty.plugins.event_type.birth import Birth
from betty.plugins.loader.gramps import FamilyTree, Gramps, GrampsConfiguration
from betty.plugins.place_type.city import City
from betty.plugins.role.subject import Subject
from betty.role import RoleManufacturer
from betty.test_utils.conftest import IsolatedProjectFactory


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
            service_plugins=[
                LoaderManufacturer(
                    Gramps.plugin(),
                    GrampsConfiguration(
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
            assert isinstance(project.ancestry[Event]["E0000"].event_type, Birth)

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
            service_plugins=[
                LoaderManufacturer(
                    Gramps.plugin(),
                    GrampsConfiguration(
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
            assert isinstance(project.ancestry[Place]["P0001"].place_type, City)

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
            service_plugins=[
                LoaderManufacturer(
                    Gramps.plugin(),
                    GrampsConfiguration(
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
                next(iter(project.ancestry[Person]["I0000"].presences)).role, Subject
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
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            gramps_family_tree_one_path = working_directory_path / "one.gramps"
            with gzip.open(gramps_family_tree_one_path, "w") as f:
                f.write(family_tree_one_xml.encode("utf-8"))

            gramps_family_tree_two_path = working_directory_path / "two.gramps"
            with gzip.open(gramps_family_tree_two_path, "w") as f:
                f.write(family_tree_two_xml.encode("utf-8"))

            async with isolated_project_factory(
                service_plugins=[
                    LoaderManufacturer(
                        Gramps.plugin(),
                        GrampsConfiguration(
                            family_trees=[
                                FamilyTree(gramps_family_tree_one_path),
                                FamilyTree(gramps_family_tree_two_path),
                            ]
                        ),
                    )
                ],
            ) as project:
                await load(project)
                assert "I0001" in project.ancestry[Person]
                assert "I0002" in project.ancestry[Person]
                assert "P0001" in project.ancestry[Place]
                assert "P0002" in project.ancestry[Place]
                assert "E0001" in project.ancestry[Event]
                assert "E0002" in project.ancestry[Event]
                assert "S0001" in project.ancestry[Source]
                assert "S0002" in project.ancestry[Source]
                assert "R0001" in project.ancestry[Source]
                assert "R0002" in project.ancestry[Source]
                assert "C0001" in project.ancestry[Citation]
                assert "C0002" in project.ancestry[Citation]
                assert "N0001" in project.ancestry[Note]
                assert "N0002" in project.ancestry[Note]
