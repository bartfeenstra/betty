from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
    Birth,
    Death,
    Unknown as UnknownEventType,
)
from betty.ancestry.file import File
from betty.ancestry.gender.genders import Unknown as UnknownGender, NonBinary
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.source import Source
from betty.app import App
from betty.copyright_notice.copyright_notices import (
    PublicDomain as PublicDomainCopyrightNotice,
)
from betty.date import Date, DateRange
from betty.gramps.error import UserFacingGrampsError
from betty.gramps.loader import GrampsLoader, LoaderUsedAlready, GrampsFileNotFound
from betty.license.licenses import PublicDomain as PublicDomainLicense
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.path import rootname
from betty.privacy import Privacy
from betty.project import Project

if TYPE_CHECKING:
    from betty.ancestry import Ancestry
    from betty.ancestry.event_type import EventType
    from betty.ancestry.gender import Gender
    from betty.ancestry.presence_role import PresenceRole
    from collections.abc import Mapping, Awaitable, Callable


class TestGrampsLoader:
    ATTRIBUTE_PREFIX_KEY = "pre3f1x"
    PROJECT_NAME = "pr0j3ct"

    async def test_load_gramps(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                localizer=DEFAULT_LOCALIZER,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            await sut.load_gramps(Path(__file__).parent / "assets" / "minimal.gramps")

    async def test_load_gramps_with_non_existent_file(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                localizer=DEFAULT_LOCALIZER,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(GrampsFileNotFound):
                await sut.load_gramps(tmp_path / "non-existent-file")

    async def test_load_gpkg(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                localizer=DEFAULT_LOCALIZER,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            await sut.load_gpkg(Path(__file__).parent / "assets" / "minimal.gpkg")

    async def test_load_gpkg_with_non_existent_file(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                localizer=DEFAULT_LOCALIZER,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(GrampsFileNotFound):
                await sut.load_gpkg(tmp_path / "non-existent-file")

    @pytest.mark.parametrize(
        "file_path",
        [
            Path(__file__).parent / "assets" / "minimal.gramps",
            Path(__file__).parent / "assets" / "minimal.gpkg",
            Path(__file__).parent / "assets" / "minimal.xml",
        ],
    )
    async def test_load_file(self, file_path: Path, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                localizer=DEFAULT_LOCALIZER,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            await sut.load_file(file_path)
            with pytest.raises(LoaderUsedAlready):
                await sut.load_file(file_path)

    async def test_load_file_with_non_existent_file(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                localizer=DEFAULT_LOCALIZER,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(GrampsFileNotFound):
                await sut.load_file(tmp_path / "non-existent-file")

    async def test_load_file_with_invalid_file(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                localizer=DEFAULT_LOCALIZER,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(UserFacingGrampsError):
                await sut.load_file(
                    Path(__file__).parent / "assets" / "minimal.invalid"
                )

    async def _load(
        self,
        xml: str,
        *,
        event_type_map: Mapping[str, Callable[[], EventType | Awaitable[EventType]]]
        | None = None,
        gender_map: Mapping[str, Callable[[], Gender | Awaitable[Gender]]]
        | None = None,
        presence_role_map: Mapping[
            str, Callable[[], PresenceRole | Awaitable[PresenceRole]]
        ]
        | None = None,
    ) -> Ancestry:
        async with (
            App.new_temporary() as app,
            app,
            Project.new_temporary(app) as project,
        ):
            project.configuration.name = self.PROJECT_NAME
            async with project:
                loader = GrampsLoader(
                    project.ancestry,
                    factory=project.new_target,
                    localizer=DEFAULT_LOCALIZER,
                    copyright_notices=project.copyright_notice_repository,
                    licenses=await project.license_repository,
                    attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
                    event_type_map=event_type_map,
                    gender_map=gender_map,
                    presence_role_map=presence_role_map,
                )
                async with TemporaryDirectory() as tree_directory_path_str:
                    await loader.load_xml(
                        xml.strip(),
                        Path(tree_directory_path_str),
                    )
                return project.ancestry

    async def _load_partial(
        self,
        xml: str,
        *,
        event_type_map: Mapping[str, Callable[[], EventType | Awaitable[EventType]]]
        | None = None,
        gender_map: Mapping[str, Callable[[], Gender | Awaitable[Gender]]]
        | None = None,
        presence_role_map: Mapping[
            str, Callable[[], PresenceRole | Awaitable[PresenceRole]]
        ]
        | None = None,
    ) -> Ancestry:
        return await self._load(
            f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/1.7.1/">
    <header>
        <created date="2019-03-09" version="4.2.8"/>
        <researcher>
        </researcher>
    </header>
    {xml}
</database>
""",
            event_type_map=event_type_map,
            gender_map=gender_map,
            presence_role_map=presence_role_map,
        )

    async def test_load_xml(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            gramps_file_path = Path(__file__).parent / "assets" / "minimal.xml"
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                localizer=DEFAULT_LOCALIZER,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            async with aiofiles.open(gramps_file_path) as f:
                await sut.load_xml(await f.read(), rootname(gramps_file_path))

    async def test_place_should_include_name(self) -> None:
        ancestry = await self._load_partial(
            """
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
        <pname value="Amsterdam"/>
    </placeobj>
</places>
        """
        )
        place = ancestry[Place]["P0000"]
        names = place.names
        assert len(names) == 1
        name = names[0]
        assert name.name.localize(DEFAULT_LOCALIZER) == "Amsterdam"

    async def test_place_should_include_note(self) -> None:
        ancestry = await self._load_partial(
            """
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
        <noteref hlink="_e1cb35d7e6c1984b0e8361e1aee"/>
    </placeobj>
</places>
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript">
        <text>I left this for you.</text>
    </note>
</notes>
"""
        )
        place = ancestry[Place]["P0000"]
        assert place.notes
        note = place.notes[0]
        assert note.id == "N0000"

    @pytest.mark.parametrize(
        ("expected_latitude", "expected_longitude", "latitude", "longitude"),
        [
            (4.9, 52.366667, "4.9", "52.366667"),
            (41.5, -81.0, "41.5", "-81.0"),
            (41.5, 81.0, "41.5 N", "-81.0 W"),
            (41.5, 81.0, "-41.5 S", "81.0 E"),
            (23.439444, 23.458333, "23 26m 22s N", "23 27m 30s E"),
            (39.333333, -74.583333, "N 39°20' 0''", "W 74°35' 0''"),
        ],
    )
    async def test_place_should_include_coordinates(
        self,
        expected_latitude: float,
        expected_longitude: float,
        latitude: str,
        longitude: str,
    ) -> None:
        ancestry = await self._load_partial(
            f"""
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
        <coord lat="{latitude}" long="{longitude}"/>
    </placeobj>
</places>
        """
        )
        coordinates = ancestry[Place]["P0000"].coordinates
        assert coordinates
        assert pytest.approx(expected_latitude) == coordinates.latitude
        assert pytest.approx(expected_longitude) == coordinates.longitude

    async def test_place_should_ignore_invalid_coordinates(self) -> None:
        ancestry = await self._load_partial(
            """
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
        <coord lat="foo" long="bar"/>
    </placeobj>
</places>
        """
        )
        coordinates = ancestry[Place]["P0000"].coordinates
        assert coordinates is None

    async def test_place_should_include_events(self) -> None:
        ancestry = await self._load_partial(
            """
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
    </placeobj>
</places>
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000">
        <type>Birth</type>
        <place hlink="_e1dd2fb639e3f04f8cfabaa7e8a"/>
    </event>
</events>
"""
        )
        place = ancestry[Place]["P0000"]
        event = ancestry[Event]["E0000"]
        assert place == event.place
        assert event in place.events

    async def test_place_should_include_encloser(self) -> None:
        ancestry = await self._load_partial(
            """
<places>
    <placeobj handle="_e7692ea23775e80643fe4fcf91" change="1552125653" id="P0000" type="Unknown">
    </placeobj>
    <placeobj handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1552125653" id="P0001" type="Unknown">
    </placeobj>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0002" type="Unknown">
        <placeref hlink="_e7692ea23775e80643fe4fcf91"/>
        <placeref hlink="_e2b5e77b4cc5c91c9ed60a6cb39"/>
    </placeobj>
</places>
"""
        )
        assert (
            ancestry[Place]["P0000"] == ancestry[Place]["P0002"].enclosers[0].encloser
        )
        assert (
            ancestry[Place]["P0001"] == ancestry[Place]["P0002"].enclosers[1].encloser
        )
        assert (
            ancestry[Place]["P0002"] == ancestry[Place]["P0000"].enclosees[0].enclosee
        )
        assert (
            ancestry[Place]["P0002"] == ancestry[Place]["P0001"].enclosees[0].enclosee
        )

    async def test_person_should_include_names(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd36c700f7fa6564d3ac839db" change="1552127019" id="I0000">
        <gender>U</gender>
        <name type="Birth Name">
            <first>Jane</first>
            <surname>Doe</surname>
            <surname prim="0">Doh</surname>
            <title>Mx</title>
            <nick>Jay</nick>
        </name>
        <name alt="1" type="Also Known As">
            <first>Jen</first>
            <surname prefix="Van">Doughie</surname>
        </name>
    </person>
</people>
"""
        )
        person = ancestry[Person]["I0000"]

        assert person.names[0].individual == "Jane"
        assert person.names[0].affiliation == "Doe"
        assert person.names[1].individual == "Jane"
        assert person.names[1].affiliation == "Doh"
        assert person.names[2].individual == "Jen"
        assert person.names[2].affiliation == "Van Doughie"

    async def test_person_should_include_presence(self) -> None:
        ancestry = await self._load_partial(
            """
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
""",
            presence_role_map={"MyFirstRole": Subject},
        )
        event = ancestry[Person]["I0000"].presences[0].event
        assert event is not None
        assert event.id == "E0000"

    async def test_person_should_be_private(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd3c1caf863ee0081cc2cc16f" change="1552131917" id="I0000" priv="1">
        <gender>U</gender>
    </person>
</people>
"""
        )
        person = ancestry[Person]["I0000"]
        assert person.private

    async def test_person_should_not_be_private(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd3bf1f0041d92f586f9d8683" change="1552126972" id="I0000">
        <gender>U</gender>
    </person>
</people>
"""
        )
        person = ancestry[Person]["I0000"]
        assert not person.private

    async def test_person_should_fallback_gender(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd3bf1f0041d92f586f9d8683" change="1552126972" id="I0000">
        <gender>U</gender>
    </person>
</people>
"""
        )
        person = ancestry[Person]["I0000"]
        assert isinstance(person.gender, UnknownGender)

    async def test_person_should_load_gender_element(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd3bf1f0041d92f586f9d8683" change="1552126972" id="I0000">
        <gender>U</gender>
    </person>
</people>
""",
            gender_map={"U": NonBinary},
        )
        person = ancestry[Person]["I0000"]
        assert isinstance(person.gender, NonBinary)

    async def test_person_should_load_gender_attribute(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd3bf1f0041d92f586f9d8683" change="1552126972" id="I0000">
        <gender>U</gender>
        <attribute type="betty:gender" value="unknown"/>
    </person>
</people>
""",
            gender_map={"U": NonBinary},
        )
        person = ancestry[Person]["I0000"]
        assert isinstance(person.gender, UnknownGender)

    async def test_person_should_include_citation(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd36c700f7fa6564d3ac839db" change="1552127019" id="I0000">
        <gender>U</gender>
        <citationref hlink="_e2c25a12a097a0b24bd9eae5090"/>
    </person>
</people>
<citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0000">
        <sourceref hlink="_e2b5e77b4cc5c91c9ed60a6cb39"/>
    </citation>
</citations>
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
    </source>
</sources>
"""
        )
        person = ancestry[Person]["I0000"]
        citation = ancestry[Citation]["C0000"]
        assert citation in person.citations

    async def test_person_should_include_note(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd36c700f7fa6564d3ac839db" change="1552127019" id="I0000">
        <gender>U</gender>
        <noteref hlink="_e1cb35d7e6c1984b0e8361e1aee"/>
    </person>
</people>
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript">
        <text>I left this for you.</text>
    </note>
</notes>
"""
        )
        person = ancestry[Person]["I0000"]
        assert person.notes
        note = person.notes[0]
        assert note.id == "N0000"

    async def test_person_should_include_file(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd36c700f7fa6564d3ac839db" change="1552127019" id="I0000">
        <gender>U</gender>
        <objref hlink="_e1cb35d7e6c1984b0e8361e1aee">
            <region corner1_x="1" corner1_y="2" corner2_x="3" corner2_y="4"/>
        </objref>
    </person>
</people>
<objects>
    <object handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="O0000">
        <file src="/tmp/file.png" mime="image/png" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
    </object>
</objects>
"""
        )
        person = ancestry[Person]["I0000"]
        assert person.file_references
        file_reference = person.file_references[0]
        assert file_reference.focus == (1, 2, 3, 4)
        assert file_reference.file.id == "O0000"

    async def test_family_should_set_parents(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd36c700f7fa6564d3ac839db" change="1552127019" id="I0000">
        <gender>U</gender>
        <childof hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
    <person handle="_e1dd3b41b052be747e10b86c4a" change="1552127019" id="I0001">
        <gender>U</gender>
        <childof hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
    <person handle="_e1dd3bf1f0041d92f586f9d8683" change="1552126972" id="I0002">
        <gender>U</gender>
        <parentin hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
    <person handle="_e1dd3c1caf863ee0081cc2cc16f" change="1552131917" id="I0003" priv="1">
        <gender>U</gender>
        <parentin hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
</people>
<families>
    <family handle="_e1dd3b84f9e5d832ffc17baa46c" change="1552127019" id="F0000">
        <rel type="Unknown"/>
        <father hlink="_e1dd3bf1f0041d92f586f9d8683"/>
        <mother hlink="_e1dd3c1caf863ee0081cc2cc16f"/>
        <childref hlink="_e1dd36c700f7fa6564d3ac839db" mrel="Unknown" frel="Unknown"/>
        <childref hlink="_e1dd3b41b052be747e10b86c4a" mrel="Unknown" frel="Unknown"/>
    </family>
</families>
"""
        )
        expected_parents = [
            ancestry[Person]["I0002"],
            ancestry[Person]["I0003"],
        ]
        children = [
            ancestry[Person]["I0000"],
            ancestry[Person]["I0001"],
        ]
        for child in children:
            assert expected_parents == list(child.parents)

    async def test_family_should_set_children(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd36c700f7fa6564d3ac839db" change="1552127019" id="I0000">
        <gender>U</gender>
        <childof hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
    <person handle="_e1dd3b41b052be747e10b86c4a" change="1552127019" id="I0001">
        <gender>U</gender>
        <childof hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
    <person handle="_e1dd3bf1f0041d92f586f9d8683" change="1552126972" id="I0002">
        <gender>U</gender>
        <parentin hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
    <person handle="_e1dd3c1caf863ee0081cc2cc16f" change="1552131917" id="I0003" priv="1">
        <gender>U</gender>
        <parentin hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
</people>
<families>
    <family handle="_e1dd3b84f9e5d832ffc17baa46c" change="1552127019" id="F0000">
        <rel type="Unknown"/>
        <father hlink="_e1dd3bf1f0041d92f586f9d8683"/>
        <mother hlink="_e1dd3c1caf863ee0081cc2cc16f"/>
        <childref hlink="_e1dd36c700f7fa6564d3ac839db" mrel="Unknown" frel="Unknown"/>
        <childref hlink="_e1dd3b41b052be747e10b86c4a" mrel="Unknown" frel="Unknown"/>
    </family>
</families>
"""
        )
        parents = [
            ancestry[Person]["I0002"],
            ancestry[Person]["I0003"],
        ]
        expected_children = [
            ancestry[Person]["I0000"],
            ancestry[Person]["I0001"],
        ]
        for parent in parents:
            assert expected_children == list(parent.children)

    async def test_event_should_map_type(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e56068c37402fda8741678a115a" change="1577021208" id="E0000">
        <type>MyFirstEventType</type>
    </event>
</events>
""",
            event_type_map={"MyFirstEventType": Birth},
        )
        assert isinstance(ancestry[Event]["E0000"].event_type, Birth)

    async def test_event_should_be_death(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e1dd6b69f2d6c31de58efd91ddf" change="1552131913" id="E0000">
        <type>Death</type>
    </event>
</events>
""",
            event_type_map={"Death": Death},
        )
        assert isinstance(ancestry[Event]["E0000"].event_type, Death)

    async def test_event_should_load_unknown(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>SomeEventThatIUsedToKnow</type>
        <dateval val="0000-00-00" quality="calculated"/>
    </event>
</events>
"""
        )
        assert isinstance(ancestry[Event]["E0000"].event_type, UnknownEventType)

    async def test_event_should_include_place(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000">
        <type>Birth</type>
        <place hlink="_e1dd2fb639e3f04f8cfabaa7e8a"/>
    </event>
</events>
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
        <pname value="Amsterdam"/>
    </placeobj>
</places>
"""
        )
        event = ancestry[Event]["E0000"]
        place = ancestry[Place]["P0000"]
        assert place == event.place

    async def test_event_should_include_date(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01"/>
    </event>
</events>
"""
        )
        event = ancestry[Event]["E0000"]
        assert isinstance(event.date, Date)
        assert event.date.year == 1970
        assert event.date.month == 1
        assert event.date.day == 1

    async def test_event_should_include_people(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd36c700f7fa6564d3ac839db" change="1552127019" id="I0000">
        <gender>U</gender>
        <eventref hlink="_e1dd3ac2fa22e6fefa18f738bdd" role="Primary"/>
    </person>
</people>
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000">
        <type>Birth</type>
    </event>
</events>
"""
        )
        event = ancestry[Event]["E0000"]
        expected_people = [ancestry[Person]["I0000"]]
        assert expected_people == [presence.person for presence in event.presences]

    async def test_event_should_include_description(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e56068c37402fda8741678a115a" change="1577021208" id="E0000">
        <type>Birth</type>
        <description>Something happened!</description>
    </event>
</events>
"""
        )
        event = ancestry[Event]["E0000"]
        assert event.description.localize(DEFAULT_LOCALIZER) == "Something happened!"

    async def test_event_should_include_note(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e56068c37402fda8741678a115a" change="1577021208" id="E0000">
        <type>Birth</type>
        <noteref hlink="_e1cb35d7e6c1984b0e8361e1aee"/>
    </event>
</events>
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript">
        <text>I left this for you.</text>
    </note>
</notes>
"""
        )
        event = ancestry[Event]["E0000"]
        assert event.notes
        note = event.notes[0]
        assert note.id == "N0000"

    @pytest.mark.parametrize(
        ("expected", "dateval_val"),
        [
            (Date(), "0000-00-00"),
            (Date(None, None, 1), "0000-00-01"),
            (Date(None, 1), "0000-01-00"),
            (Date(None, 1, 1), "0000-01-01"),
            (Date(1970), "1970-00-00"),
            (Date(1970, None, 1), "1970-00-01"),
            (Date(1970, 1), "1970-01-00"),
            (Date(1970, 1, 1), "1970-01-01"),
        ],
    )
    async def test_date_should_load_parts(
        self, expected: Date, dateval_val: str
    ) -> None:
        ancestry = await self._load_partial(
            f"""
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="{dateval_val}" quality="calculated"/>
    </event>
</events>
"""
        )
        assert expected == ancestry[Event]["E0000"].date

    async def test_date_should_ignore_calendar_format(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e560a44fed046f2f2d58662aac9" change="1576270227" id="E0000">
      <type>Birth</type>
      <dateval val="1349-01-01" cformat="Persian"/>
    </event>
</events>
"""
        )
        assert ancestry[Event]["E0000"].date is None

    async def test_date_should_load_before(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" type="before"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, DateRange)
        assert date.start is None
        assert date.end is not None
        assert date.end.year == 1970
        assert date.end.month == 1
        assert date.end.day == 1
        assert date.end_is_boundary
        assert not date.end.fuzzy

    async def test_date_should_load_after(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" type="after"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, DateRange)
        assert date.start is not None
        assert date.end is None
        assert date.start.year == 1970
        assert date.start.month == 1
        assert date.start.day == 1
        assert date.start_is_boundary
        assert not date.start.fuzzy

    async def test_date_should_load_calculated(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" quality="calculated"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, Date)
        assert date.year == 1970
        assert date.month == 1
        assert date.day == 1
        assert not date.fuzzy

    async def test_date_should_load_estimated(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" quality="estimated"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, Date)
        assert date.year == 1970
        assert date.month == 1
        assert date.day == 1
        assert date.fuzzy

    async def test_date_should_load_about(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="1970-01-01" type="about"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, Date)
        assert date.year == 1970
        assert date.month == 1
        assert date.day == 1
        assert date.fuzzy

    async def test_daterange_should_load(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        end = date.end
        assert isinstance(end, Date)
        assert start.year == 1970
        assert start.month == 1
        assert start.day == 1
        assert not start.fuzzy
        assert date.start_is_boundary
        assert end.year == 1999
        assert end.month == 12
        assert end.day == 31
        assert date.end_is_boundary
        assert not end.fuzzy

    async def test_daterange_should_load_calculated(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31" quality="calculated"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        assert not start.fuzzy
        end = date.end
        assert isinstance(end, Date)
        assert not end.fuzzy

    async def test_daterange_should_load_estimated(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <daterange start="1970-01-01" stop="1999-12-31" quality="estimated"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        assert start.fuzzy
        end = date.end
        assert isinstance(end, Date)
        assert end.fuzzy

    async def test_datespan_should_load(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        end = date.end
        assert isinstance(end, Date)
        assert start.year == 1970
        assert start.month == 1
        assert start.day == 1
        assert not start.fuzzy
        assert end.year == 1999
        assert end.month == 12
        assert end.day == 31
        assert not end.fuzzy

    async def test_datespan_should_load_calculated(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31" quality="calculated"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        assert not start.fuzzy
        end = date.end
        assert isinstance(end, Date)
        assert not end.fuzzy

    async def test_datespan_should_load_estimated(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <datespan start="1970-01-01" stop="1999-12-31" quality="estimated"/>
    </event>
</events>
"""
        )
        date = ancestry[Event]["E0000"].date
        assert isinstance(date, DateRange)
        start = date.start
        assert isinstance(start, Date)
        assert start.fuzzy
        end = date.end
        assert isinstance(end, Date)
        assert end.fuzzy

    async def test_source_from_repository_should_include_name(self) -> None:
        ancestry = await self._load_partial(
            """
<repositories>
    <repository handle="_e2c257f50fd27b1c841d7497448" change="1558277216" id="R0000">
        <rname>Library of Alexandria</rname>
    </repository>
</repositories>
"""
        )
        source = ancestry[Source]["R0000"]
        assert source.name.localize(DEFAULT_LOCALIZER) == "Library of Alexandria"

    async def test_source_from_repository_should_include_link(self) -> None:
        ancestry = await self._load_partial(
            """
<repositories>
    <repository handle="_e2c257f50fd27b1c841d7497448" change="1558277216" id="R0000">
        <rname>Library of Alexandria</rname>
        <url href="https://alexandria.example.com" type="Unknown" description="Library of Alexandria Catalogue"/>
    </repository>
</repositories>
"""
        )
        links = ancestry[Source]["R0000"].links
        assert len(links) == 1
        link = list(links)[0]
        assert link.url == "https://alexandria.example.com"
        assert (
            link.label.localize(DEFAULT_LOCALIZER) == "Library of Alexandria Catalogue"
        )

    async def test_source_from_source_should_include_title(self) -> None:
        ancestry = await self._load_partial(
            """
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
        <stitle>A Whisper</stitle>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert source.name.localize(DEFAULT_LOCALIZER) == "A Whisper"

    async def test_source_from_source_should_include_author(self) -> None:
        ancestry = await self._load_partial(
            """
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
        <sauthor>A Little Birdie</sauthor>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert source.author.localize(DEFAULT_LOCALIZER) == "A Little Birdie"

    async def test_source_from_source_should_include_publisher(self) -> None:
        ancestry = await self._load_partial(
            """
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
        <spubinfo>Somewhere over the rainbow</spubinfo>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert (
            source.publisher.localize(DEFAULT_LOCALIZER) == "Somewhere over the rainbow"
        )

    async def test_source_from_source_should_include_repository(self) -> None:
        ancestry = await self._load_partial(
            """
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
        <reporef hlink="_e2c257f50fd27b1c841d7497448" medium="Book"/>
    </source>
</sources>
<repositories>
    <repository handle="_e2c257f50fd27b1c841d7497448" change="1558277216" id="R0000">
        <rname>Library of Alexandria</rname>
        <type>Unknown</type>
        <url href="https://alexandria.example.com" type="Unknown" description="Library of Alexandria Catalogue"/>
    </repository>
</repositories>
"""
        )
        source = ancestry[Source]["S0000"]
        containing_source = ancestry[Source]["R0000"]
        assert containing_source == source.contained_by

    async def test_source_from_repository_should_include_note(self) -> None:
        ancestry = await self._load_partial(
            """
<repositories>
    <repository handle="_e2c257f50fd27b1c841d7497448" change="1558277216" id="R0000">
        <rname>Library of Alexandria</rname>
        <noteref hlink="_e1cb35d7e6c1984b0e8361e1aee"/>
    </repository>
</repositories>
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript">
        <text>I left this for you.</text>
    </note>
</notes>
"""
        )
        source = ancestry[Source]["R0000"]
        assert source.notes
        note = source.notes[0]
        assert note.id == "N0000"

    async def test_source_from_source_should_include_note(self) -> None:
        ancestry = await self._load_partial(
            """
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
        <noteref hlink="_e1cb35d7e6c1984b0e8361e1aee"/>
    </source>
</sources>
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript">
        <text>I left this for you.</text>
    </note>
</notes>
"""
        )
        source = ancestry[Source]["S0000"]
        assert source.notes
        note = source.notes[0]
        assert note.id == "N0000"

    async def test_source_from_source_should_include_attribute_links(self) -> None:
        link_minimal_url = "http://example.com"
        link_full_url = "https://example.com"
        link_full_description = "Check out the world's Example Domain!"
        link_full_label = "Example.com"
        link_full_locale = "en"
        link_full_media_type = "text/plain"
        link_full_relationship = "external"
        ancestry = await self._load_partial(
            f"""
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
      <srcattribute type="betty:link-minimal:url" value="{link_minimal_url}"/>
      <srcattribute type="betty:link-full:url" value="{link_full_url}"/>
      <srcattribute type="betty:link-full:description" value="{link_full_description}"/>
      <srcattribute type="betty:link-full:label" value="{link_full_label}"/>
      <srcattribute type="betty:link-full:locale" value="{link_full_locale}"/>
      <srcattribute type="betty:link-full:media_type" value="{link_full_media_type}"/>
      <srcattribute type="betty:link-full:relationship" value="{link_full_relationship}"/>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert source.links
        link_minimal = source.links[0]
        link_full = source.links[1]
        assert link_minimal.url == link_minimal_url
        assert not link_minimal.description
        assert not link_minimal.label
        assert link_minimal.locale is UNDETERMINED_LOCALE
        assert link_minimal.media_type is None
        assert link_minimal.relationship is None
        assert link_full.url == link_full_url
        assert (
            link_full.description.localize(DEFAULT_LOCALIZER) == link_full_description
        )
        assert link_full.label.localize(DEFAULT_LOCALIZER) == link_full_label
        assert link_full.locale == link_full_locale
        assert link_full.media_type == MediaType(link_full_media_type)
        assert link_full.relationship == link_full_relationship

    async def test_source_from_source_should_warn_about_attribute_link_without_url(
        self,
    ) -> None:
        ancestry = await self._load_partial(
            """
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
      <srcattribute type="betty:link-invalid:label" value="Example.com"/>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert not source.links

    async def test_source_from_source_should_warn_about_attribute_link_invalid_media_type(
        self,
    ) -> None:
        ancestry = await self._load_partial(
            """
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
      <srcattribute type="betty:link-one:url" value="https://example.com"/>
      <srcattribute type="betty:link-one:media_type" value="not-a-valid-media-type"/>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert source.links
        link_one = source.links[0]
        assert link_one.media_type is None

    @pytest.mark.parametrize(
        ("expected", "global_attribute_value", "project_attribute_value"),
        [
            # Global attributes only.
            (Privacy.PRIVATE, "private", None),
            (Privacy.PUBLIC, "public", None),
            (Privacy.UNDETERMINED, "publi", None),
            (Privacy.UNDETERMINED, "privat", None),
            # Project-specific attributes only.
            (Privacy.PRIVATE, None, "private"),
            (Privacy.PUBLIC, None, "public"),
            (Privacy.UNDETERMINED, None, "publi"),
            (Privacy.UNDETERMINED, None, "privat"),
            # Project-specific attributes overriding global ones.
            (Privacy.PRIVATE, "public", "private"),
            (Privacy.PUBLIC, "private", "public"),
        ],
    )
    async def test_person_should_include_privacy_from_attribute(
        self,
        expected: Privacy,
        global_attribute_value: str | None,
        project_attribute_value: str | None,
    ) -> None:
        global_attribute = (
            ""
            if global_attribute_value is None
            else f'<attribute type="betty:privacy" value="{global_attribute_value}"/>'
        )
        project_attribute = (
            ""
            if project_attribute_value is None
            else f'<attribute type="betty-{self.ATTRIBUTE_PREFIX_KEY}:privacy" value="{project_attribute_value}"/>'
        )
        ancestry = await self._load_partial(
            f"""
<people>
    <person handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="I0000">
        <gender>U</gender>
        {global_attribute}
        {project_attribute}
    </person>
</people>
"""
        )
        person = ancestry[Person]["I0000"]
        assert expected == person.privacy

    @pytest.mark.parametrize(
        ("expected", "attribute_value"),
        [
            (Privacy.PRIVATE, "private"),
            (Privacy.PUBLIC, "public"),
            (Privacy.UNDETERMINED, "publi"),
            (Privacy.UNDETERMINED, "privat"),
        ],
    )
    async def test_event_should_include_privacy_from_attribute(
        self, expected: Privacy, attribute_value: str
    ) -> None:
        ancestry = await self._load_partial(
            f"""
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000">
        <type>Birth</type>
        <attribute type="betty:privacy" value="{attribute_value}"/>
    </event>
</events>
"""
        )
        event = ancestry[Event]["E0000"]
        assert expected == event.privacy

    @pytest.mark.parametrize(
        ("expected", "attribute_value"),
        [
            (Privacy.PRIVATE, "private"),
            (Privacy.PUBLIC, "public"),
            (Privacy.UNDETERMINED, "publi"),
            (Privacy.UNDETERMINED, "privat"),
        ],
    )
    async def test_file_should_include_privacy_from_attribute(
        self, expected: Privacy, attribute_value: str
    ) -> None:
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="/tmp/file.txt" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
        <attribute type="betty:privacy" value="{attribute_value}"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert expected == file.privacy

    async def test_file_should_include_note(self) -> None:
        ancestry = await self._load_partial(
            """
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="/tmp/file.txt" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
        <noteref hlink="_e1cb35d7e6c1984b0e8361e1aee"/>
    </object>
</objects>
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript">
        <text>I left this for you.</text>
    </note>
</notes>
"""
        )
        file = ancestry[File]["O0000"]
        assert file.notes
        note = file.notes[0]
        assert note.id == "N0000"

    async def test_file_should_include_copyright_notice(self) -> None:
        ancestry = await self._load_partial(
            """
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="/tmp/file.txt" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
        <attribute type="betty:copyright-notice" value="public-domain"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert isinstance(file.copyright_notice, PublicDomainCopyrightNotice)

    async def test_file_should_ignore_unknown_copyright_notice(self) -> None:
        ancestry = await self._load_partial(
            """
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="/tmp/file.txt" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
        <attribute type="betty:copyright-notice" value="non-existent-copyright-notice"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert file.copyright_notice is None

    async def test_file_should_include_license(self) -> None:
        ancestry = await self._load_partial(
            """
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="/tmp/file.txt" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
        <attribute type="betty:license" value="public-domain"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert isinstance(file.license, PublicDomainLicense)

    async def test_file_should_ignore_unknown_license(self) -> None:
        ancestry = await self._load_partial(
            """
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="/tmp/file.txt" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="file"/>
        <attribute type="betty:license" value="non-existent-license"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert file.license is None

    @pytest.mark.parametrize(
        ("expected", "attribute_value"),
        [
            (Privacy.PRIVATE, "private"),
            (Privacy.PUBLIC, "public"),
            (Privacy.UNDETERMINED, "publi"),
            (Privacy.UNDETERMINED, "privat"),
        ],
    )
    async def test_source_from_source_should_include_privacy_from_attribute(
        self, expected: Privacy, attribute_value: str
    ) -> None:
        ancestry = await self._load_partial(
            f"""
<sources>
    <source handle="_e1dd686b04813540eb3503a342b" change="1558277217" id="S0000">
        <stitle>A Whisper</stitle>
        <srcattribute type="betty:privacy" value="{attribute_value}"/>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert expected == source.privacy

    @pytest.mark.parametrize(
        ("expected", "attribute_value"),
        [
            (Privacy.PRIVATE, "private"),
            (Privacy.PUBLIC, "public"),
            (Privacy.UNDETERMINED, "publi"),
            (Privacy.UNDETERMINED, "privat"),
        ],
    )
    async def test_citation_should_include_privacy_from_attribute(
        self, expected: Privacy, attribute_value: str
    ) -> None:
        ancestry = await self._load_partial(
            f"""
<citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0000">
        <confidence>2</confidence>
        <sourceref hlink="_e1dd686b04813540eb3503a342b"/>
        <srcattribute type="betty:privacy" value="{attribute_value}"/>
    </citation>
</citations>
<sources>
    <source handle="_e1dd686b04813540eb3503a342b" change="1558277217" id="S0000">
        <stitle>A Whisper</stitle>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        source.public = True
        citation = ancestry[Citation]["C0000"]
        assert expected == citation.privacy

    async def test_note_should_include_text(self) -> None:
        ancestry = await self._load_partial(
            """
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript">
        <text>I left this for you.</text>
    </note>
</notes>
"""
        )
        note = ancestry[Note]["N0000"]
        assert note.text.localize(DEFAULT_LOCALIZER) == "I left this for you."

    async def test_citation_should_include_location_from_place(self) -> None:
        ancestry = await self._load_partial(
            """
<citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0000">
        <confidence>2</confidence>
        <sourceref hlink="_e1dd686b04813540eb3503a342b"/>
        <page>My First Page</page>
    </citation>
</citations>
<sources>
    <source handle="_e1dd686b04813540eb3503a342b" change="1558277217" id="S0000">
        <stitle>A Whisper</stitle>
    </source>
</sources>
"""
        )
        citation = ancestry[Citation]["C0000"]
        assert citation.location.localize(DEFAULT_LOCALIZER) == "My First Page"

    async def test__load_eventref_should_map_presence_role(self) -> None:
        ancestry = await self._load_partial(
            """
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
""",
            presence_role_map={"MyFirstRole": Subject},
        )
        person = ancestry[Person]["I0000"]
        presence = person.presences[0]
        assert isinstance(presence.role, Subject)

    async def test__load_eventref_should_include_privacy(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd3c1caf863ee0081cc2cc16f" change="1552131917" id="I0000">
        <gender>U</gender>
        <eventref hlink="_e7692ea23775e80643fe4fcf91" priv="1" role="Primary"/>
    </person>
</people>
<events>
    <event handle="_e7692ea23775e80643fe4fcf91" change="1590243374" id="E0000">
        <type>Birth</type>
        <dateval val="0000-00-00" quality="calculated"/>
    </event>
</events>
"""
        )
        person = ancestry[Person]["I0000"]
        presence = person.presences[0]
        assert presence.private
