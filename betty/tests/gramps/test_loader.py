from __future__ import annotations

import gzip
import tarfile
from asyncio.subprocess import Process
from gettext import NullTranslations
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest
from aiofiles.tempfile import AiofilesContextManagerTempDir
from babel import Locale

import betty.plugin.repository.provider.service
from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import (
    Birth,
    Death,
)
from betty.ancestry.event_type.event_types import (
    Unknown as UnknownEventType,
)
from betty.ancestry.file import File
from betty.ancestry.gender import GenderDefinition
from betty.ancestry.gender.genders import NonBinary
from betty.ancestry.gender.genders import Unknown as UnknownGender
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.place_type.place_types import City
from betty.ancestry.place_type.place_types import Unknown as UnknownPlaceType
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.source import Source
from betty.app import App
from betty.copyright_notice import CopyrightNoticeDefinition
from betty.copyright_notice.copyright_notices import (
    PublicDomain as PublicDomainCopyrightNotice,
)
from betty.date import Date, DateRange
from betty.gramps.error import UserFacingGrampsError
from betty.gramps.loader import GrampsFileNotFound, GrampsLoader, LoaderUsedAlready
from betty.license import LicenseDefinition
from betty.license.licenses import PublicDomain as PublicDomainLicense
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.media_type import MediaType
from betty.plugin.repository.static import StaticPluginRepository
from betty.privacy import Privacy
from betty.project import Project
from betty.subprocess import CalledSubprocessError
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping

    from pytest_mock import MockerFixture

    from betty.ancestry import Ancestry
    from betty.ancestry.event_type import EventType
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.presence_role import PresenceRole

__MINIMAL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML {version}//EN"
"http://gramps-project.org/xml/{version}/grampsxml.dtd">
<database xmlns="http://gramps-project.org/xml/{version}/">
  <header>
    <created date="2019-03-29" version="4.2.8"/>
    <researcher>
    </researcher>
  </header>
</database>
"""


def _minimal_xml(version: str = "1.7.1") -> str:
    return __MINIMAL_XML.format(version=version)


_MINIMAL_GED = """
0 HEAD
1 SOUR PAF
2 NAME Personal Ancestral File
2 VERS 5.0
1 DATE 30 NOV 2000
1 GEDC
2 VERS 5.5
2 FORM LINEAGE-LINKED
1 CHAR ANSEL
1 SUBM @U1@
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
1 FAMS @F1@
0 @I2@ INDI
1 NAME Elizabeth /Stansfield/
1 SEX F
1 FAMS @F1@
0 @I3@ INDI
1 NAME James /Smith/
1 SEX M
1 FAMC @F1@
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
1 CHIL @I3@
0 @U1@ SUBM
1 NAME Submitter
0 TRLR
"""


class TestGrampsLoader:
    ATTRIBUTE_PREFIX_KEY = "pre3f1x"
    PROJECT_NAME = "pr0j3ct"

    async def test_load_gramps(self, isolated_app: App, tmp_path: Path) -> None:
        gramps_file_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_file_path, "w") as f:
            f.write(_minimal_xml().encode("utf-8"))
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            await sut.load_gramps(gramps_file_path)

    async def test_load_gramps__with_non_existent_file(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(GrampsFileNotFound):
                await sut.load_gramps(tmp_path / "non-existent-file")

    async def test_load_gpkg(self, isolated_app: App, tmp_path: Path) -> None:
        gramps_file_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_file_path, "w") as f:
            f.write(_minimal_xml().encode("utf-8"))
        gpkg_file_path = tmp_path / "gramps.gpkg"
        with tarfile.open(  # noqa: SIM115
            name=gpkg_file_path, mode="w:gz"
        ) as tar_file:
            tar_file.add(gramps_file_path, "/data.gramps")
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            await sut.load_gpkg(gpkg_file_path)

    async def test_load_gpkg__with_non_existent_file(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(GrampsFileNotFound):
                await sut.load_gpkg(tmp_path / "non-existent-file")

    async def test_load_file__with_gramps(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        gramps_file_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_file_path, "w") as f:
            f.write(_minimal_xml().encode("utf-8"))
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            await sut.load_file(gramps_file_path)
            with pytest.raises(LoaderUsedAlready):
                await sut.load_file(gramps_file_path)

    async def test_load_file__with_gpkg(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        gramps_file_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_file_path, "w") as f:
            f.write(_minimal_xml().encode("utf-8"))
        gpkg_file_path = tmp_path / "gramps.gpkg"
        with tarfile.open(  # noqa: SIM115
            name=gpkg_file_path, mode="w:gz"
        ) as tar_file:
            tar_file.add(gramps_file_path, "/data.gramps")
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            await sut.load_file(gpkg_file_path)
            with pytest.raises(LoaderUsedAlready):
                await sut.load_file(gpkg_file_path)

    async def test_load_file__with_ged(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        gramps_executable = "gramps"
        ged_file_path = Path("my-first-family-tree.ged")
        m_aiofiles_context_manager_temp_dir = mocker.AsyncMock(
            spec=AiofilesContextManagerTempDir
        )
        m_aiofiles_context_manager_temp_dir.__aenter__.return_value = str(tmp_path)
        mocker.patch(
            "aiofiles.tempfile.TemporaryDirectory",
            side_effect=lambda: m_aiofiles_context_manager_temp_dir,
        )
        m_run_process = mocker.patch("betty.subprocess.run_process")
        m_run_process.side_effect = mocker.AsyncMock(spec=Process)
        gramps_file_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_file_path, "w") as f:
            f.write(_minimal_xml().encode("utf-8"))
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
                executable=gramps_executable,
            )
            await sut.load_file(ged_file_path)
        m_run_process.assert_awaited()

    async def test_load_file__with_non_existent_file(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(UserFacingGrampsError):
                await sut.load_file(tmp_path / "non-existent-file")

    async def test_load_file__with_invalid_file(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(UserFacingGrampsError):
                await sut.load_file(
                    Path(__file__).parent / "assets" / "minimal.invalid"
                )

    async def test_load_name__with_existent_family_tree(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        gramps_executable = "gramps"
        family_tree_name = "my-first-family-tree"
        m_aiofiles_context_manager_temp_dir = mocker.AsyncMock(
            spec=AiofilesContextManagerTempDir
        )
        m_aiofiles_context_manager_temp_dir.__aenter__.return_value = str(tmp_path)
        mocker.patch(
            "aiofiles.tempfile.TemporaryDirectory",
            side_effect=lambda: m_aiofiles_context_manager_temp_dir,
        )
        m_run_process = mocker.patch("betty.subprocess.run_process")
        m_run_process.side_effect = mocker.AsyncMock(spec=Process)
        gramps_file_path = tmp_path / "betty.gramps"
        with gzip.open(gramps_file_path, "w") as f:
            f.write(_minimal_xml().encode("utf-8"))
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
                executable=gramps_executable,
            )
            await sut.load_name(family_tree_name)
        m_run_process.assert_awaited_once_with(
            [gramps_executable, "-O", family_tree_name, "-e", str(gramps_file_path)],
            user=ANY,
        )

    async def test_load_name__with_non_existent_family_tree(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        gramps_executable = "gramps"
        family_tree_name = "my-first-family-tree"
        m_aiofiles_context_manager_temp_dir = mocker.AsyncMock(
            spec=AiofilesContextManagerTempDir
        )
        m_aiofiles_context_manager_temp_dir.__aenter__.return_value = str(tmp_path)
        mocker.patch(
            "aiofiles.tempfile.TemporaryDirectory",
            side_effect=lambda: m_aiofiles_context_manager_temp_dir,
        )
        m_run_process = mocker.patch("betty.subprocess.run_process")
        m_run_process.side_effect = CalledSubprocessError(1, "", "", "")
        gramps_file_path = tmp_path / "betty.gramps"
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
                executable=gramps_executable,
            )
            with pytest.raises(UserFacingGrampsError):
                await sut.load_name(family_tree_name)
        m_run_process.assert_awaited_once_with(
            [gramps_executable, "-O", family_tree_name, "-e", str(gramps_file_path)],
            user=ANY,
        )

    async def _load(
        self,
        xml: str,
        *,
        event_type_mapping: Mapping[str, Callable[[], EventType | Awaitable[EventType]]]
        | None = None,
        place_type_mapping: Mapping[str, Callable[[], PlaceType | Awaitable[PlaceType]]]
        | None = None,
        presence_role_mapping: Mapping[
            str, Callable[[], PresenceRole | Awaitable[PresenceRole]]
        ]
        | None = None,
    ) -> Ancestry:
        async with (
            App.new_isolated() as app,
            app,
            Project.new_isolated(app) as project,
        ):
            project.configuration.name = self.PROJECT_NAME
            async with project:
                loader = GrampsLoader(
                    project.ancestry,
                    factory=project.new_target,
                    user=StaticUser(),
                    copyright_notices=await betty.plugin.repository.provider.service.plugins(
                        CopyrightNoticeDefinition
                    ),
                    licenses=await betty.plugin.repository.provider.service.plugins(
                        LicenseDefinition
                    ),
                    genders=await betty.plugin.repository.provider.service.plugins(
                        GenderDefinition
                    ),
                    attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
                    event_type_mapping=event_type_mapping,
                    place_type_mapping=place_type_mapping,
                    presence_role_mapping=presence_role_mapping,
                )
                await loader.load_xml(xml.strip())
                return project.ancestry

    async def _load_partial(
        self,
        xml: str,
        *,
        media_path: Path | None = None,
        event_type_mapping: Mapping[str, Callable[[], EventType | Awaitable[EventType]]]
        | None = None,
        place_type_mapping: Mapping[str, Callable[[], PlaceType | Awaitable[PlaceType]]]
        | None = None,
        presence_role_mapping: Mapping[
            str, Callable[[], PresenceRole | Awaitable[PresenceRole]]
        ]
        | None = None,
    ) -> Ancestry:
        mediapath = "" if media_path is None else f"<mediapath>{media_path}</mediapath>"
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
        {mediapath}
    </header>
    {xml}
</database>
""",
            event_type_mapping=event_type_mapping,
            place_type_mapping=place_type_mapping,
            presence_role_mapping=presence_role_mapping,
        )

    async def test_load_xml(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            await sut.load_xml(_minimal_xml())

    @pytest.mark.parametrize(
        "version",
        [
            "1.7.0",
            "1.8.0",
            "2.0.0",
        ],
    )
    async def test_load_xml_with_unsupported_version_should_error(
        self, isolated_app: App, version: str
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(UserFacingGrampsError):
                await sut.load_xml(_minimal_xml(version))

    async def test_load_xml_with_invalid_xml_should_error(
        self, isolated_app: App
    ) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE database PUBLIC "-//Gramps//DTD Gramps XML 1.7.1//EN"
"http://gramps-project.org/xml/1.7.1/grampsxml.dtd">
<database>
  <header>
    <created date="2019-03-29" version="4.2.8"/>
    <researcher>
    </researcher>
  </header>
</database>
"""
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=StaticUser(),
                copyright_notices=await betty.plugin.repository.provider.service.plugins(
                    CopyrightNoticeDefinition
                ),
                licenses=await betty.plugin.repository.provider.service.plugins(
                    LicenseDefinition
                ),
                genders=await betty.plugin.repository.provider.service.plugins(
                    GenderDefinition
                ),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            with pytest.raises(UserFacingGrampsError):
                await sut.load_xml(xml)

    async def test_place_should_include_place_type(self) -> None:
        ancestry = await self._load_partial(
            """
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="MyFirstPlaceType">
        <pname value="Amsterdam"/>
    </placeobj>
</places>
        """,
            place_type_mapping={"MyFirstPlaceType": City},
        )
        place = ancestry[Place]["P0000"]
        assert isinstance(place.place_type, City)

    async def test_place_should_ignore_unknown_place_type(self) -> None:
        ancestry = await self._load_partial(
            """
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="NonExistentPlaceType">
        <pname value="Amsterdam"/>
    </placeobj>
</places>
        """
        )
        place = ancestry[Place]["P0000"]
        assert isinstance(place.place_type, UnknownPlaceType)

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

    async def test_place_should_include_name_with_locale(self) -> None:
        ancestry = await self._load_partial(
            """
<places>
    <placeobj handle="_e1dd2fb639e3f04f8cfabaa7e8a" change="1552125653" id="P0000" type="Unknown">
        <pname value="Amsterdam" lang="nl"/>
    </placeobj>
</places>
        """
        )
        place = ancestry[Place]["P0000"]
        names = place.names
        name = names[0]
        assert name.name.localize(DEFAULT_LOCALIZER).locale == Locale("nl")

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
        note = list(place.notes)[0]
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
            ancestry[Place]["P0000"]
            == list(ancestry[Place]["P0002"].enclosers)[0].encloser
        )
        assert (
            ancestry[Place]["P0001"]
            == list(ancestry[Place]["P0002"].enclosers)[1].encloser
        )
        assert (
            ancestry[Place]["P0002"]
            == list(ancestry[Place]["P0000"].enclosees)[0].enclosee
        )
        assert (
            ancestry[Place]["P0002"]
            == list(ancestry[Place]["P0001"].enclosees)[0].enclosee
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
        <name alt="1" type="Also Known As">
            <first>Jean</first>
        </name>
        <name alt="1" type="Also Known As">
            <surname>Doewie</surname>
        </name>
    </person>
</people>
"""
        )
        person = ancestry[Person]["I0000"]

        assert list(person.names)[0].individual == "Jane"
        assert list(person.names)[0].affiliation == "Doe"
        assert list(person.names)[1].individual == "Jane"
        assert list(person.names)[1].affiliation == "Doh"
        assert list(person.names)[2].individual == "Jen"
        assert list(person.names)[2].affiliation == "Van Doughie"
        assert list(person.names)[3].individual == "Jean"
        assert list(person.names)[4].affiliation == "Doewie"

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
            presence_role_mapping={"MyFirstRole": Subject},
        )
        event = list(ancestry[Person]["I0000"].presences)[0].event
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
        <gender>X</gender>
    </person>
</people>
"""
        )
        person = ancestry[Person]["I0000"]
        assert isinstance(person.gender, NonBinary)

    async def test_person_should_load_gender_attribute(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd3bf1f0041d92f586f9d8683" change="1552126972" id="I0000">
        <gender>U</gender>
        <attribute type="betty:gender" value="non-binary"/>
    </person>
</people>
"""
        )
        person = ancestry[Person]["I0000"]
        assert isinstance(person.gender, NonBinary)

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
        note = list(person.notes)[0]
        assert note.id == "N0000"

    async def test_person_should_include_file(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<people>
    <person handle="_e1dd36c700f7fa6564d3ac839db" change="1552127019" id="I0000">
        <gender>U</gender>
        <objref hlink="_e1cb35d7e6c1984b0e8361e1aee">
        </objref>
    </person>
</people>
<objects>
    <object handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="O0000">
        <file src="{file_path}" mime="image/png" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
    </object>
</objects>
"""
        )
        person = ancestry[Person]["I0000"]
        assert person.file_references
        file_reference = list(person.file_references)[0]
        assert file_reference.file.id == "O0000"

    async def test_person_should_include_file_with_focus(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
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
        <file src="{file_path}" mime="image/png" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
    </object>
</objects>
"""
        )
        person = ancestry[Person]["I0000"]
        assert person.file_references
        file_reference = list(person.file_references)[0]
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
        <mother hlink="_e1dd36c700f7fa6564d3ac839db"/>
        <childref hlink="_e1dd3b41b052be747e10b86c4a" mrel="Unknown" frel="Unknown"/>
    </family>
    <family handle="_e1dd6b69f2d6c31de58efd91ddf" change="1552127019" id="F0001">
        <rel type="Unknown"/>
        <father hlink="_e1dd3bf1f0041d92f586f9d8683"/>
        <mother hlink="_e1dd3c1caf863ee0081cc2cc16f"/>
        <childref hlink="_e1dd3b41b052be747e10b86c4a" mrel="Unknown" frel="Unknown"/>
    </family>
</families>
"""
        )
        father = ancestry[Person]["I0002"]
        mother_one = ancestry[Person]["I0000"]
        mother_two = ancestry[Person]["I0003"]
        child = ancestry[Person]["I0001"]
        assert list(child.parents) == [father, mother_one, mother_two]

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
    </family>
    <family handle="_e1dd6b69f2d6c31de58efd91ddf" change="1552127019" id="F0001">
        <rel type="Unknown"/>
        <mother hlink="_e1dd3c1caf863ee0081cc2cc16f"/>
        <childref hlink="_e1dd3b41b052be747e10b86c4a" mrel="Unknown" frel="Unknown"/>
    </family>
</families>
"""
        )
        father = ancestry[Person]["I0002"]
        mother = ancestry[Person]["I0003"]
        common_child = ancestry[Person]["I0000"]
        mother_only_child = ancestry[Person]["I0001"]
        assert list(father.children) == [common_child]
        assert list(mother.children) == [common_child, mother_only_child]

    async def test_family_should_associate_events_with_parents(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e1dd3bf1f0041d92f586f9d8683" change="1552126972" id="I0000">
        <gender>U</gender>
        <parentin hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
    <person handle="_e1dd3c1caf863ee0081cc2cc16f" change="1552131917" id="I0001">
        <gender>U</gender>
        <parentin hlink="_e1dd3b84f9e5d832ffc17baa46c"/>
    </person>
</people>
<families>
    <family handle="_e1dd3b84f9e5d832ffc17baa46c" change="1552127019" id="F0000">
        <rel type="Unknown"/>
        <father hlink="_e1dd3bf1f0041d92f586f9d8683"/>
        <mother hlink="_e1dd3c1caf863ee0081cc2cc16f"/>
        <eventref hlink="_e1dd3ac2fa22e6fefa18f738bdd" role="Primary"/>
    </family>
</families>
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000">
        <type>Birth</type>
    </event>
</events>
""",
            presence_role_mapping={"Primary": Subject},
        )
        event = ancestry[Event]["E0000"]
        father = ancestry[Person]["I0000"]
        assert isinstance(list(father.presences)[0].role, Subject)
        assert list(father.presences)[0].event is event
        mother = ancestry[Person]["I0001"]
        assert isinstance(list(mother.presences)[0].role, Subject)
        assert list(mother.presences)[0].event is event

    async def test_event_should_map_type(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e56068c37402fda8741678a115a" change="1577021208" id="E0000">
        <type>MyFirstEventType</type>
    </event>
</events>
""",
            event_type_mapping={"MyFirstEventType": Birth},
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
            event_type_mapping={"Death": Death},
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

    async def test_event_should_include_name(self) -> None:
        name_nl = "Een of andere naam"
        name_default = "Some name"
        ancestry = await self._load_partial(
            f"""
<events>
    <event handle="_e56068c37402fda8741678a115a" change="1577021208" id="E0000">
        <type>Birth</type>
        <attribute type="betty:name" value="{name_default}"/>
        <attribute type="betty:name:nl" value="{name_nl}"/>
    </event>
</events>
"""
        )
        event = ancestry[Event]["E0000"]
        assert event.name is not None
        assert event.name.localize(DEFAULT_LOCALIZER) == name_default
        assert event.name.localize(Localizer("nl", NullTranslations())) == name_nl

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
        assert event.description is not None
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
        note = list(event.notes)[0]
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
        assert source.name is not None
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
        assert link.url.localize(DEFAULT_LOCALIZER) == "https://alexandria.example.com"
        assert link.label is not None
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
        assert source.name is not None
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
        assert source.author is not None
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
        assert source.publisher is not None
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
        note = list(source.notes)[0]
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
        note = list(source.notes)[0]
        assert note.id == "N0000"

    async def test__load_attribute_links_should_include_attribute_links_minimal(
        self,
    ) -> None:
        url = "http://example.com"
        ancestry = await self._load_partial(
            f"""
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
      <srcattribute type="betty:link-minimal:url" value="{url}"/>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert source.links
        link = source.links.view[0]
        assert link.url.localize(DEFAULT_LOCALIZER) == url
        assert not link.description
        assert not link.has_label
        assert link.media_type is None
        assert link.relationship is None

    async def test__load_attribute_links_should_include_attribute_links_full(
        self,
    ) -> None:
        url_nl = "https://nl.example.com"
        url_undetermined = "https://example.com"
        label_nl = "Dit is een link"
        label_undetermined = "This is a link"
        description_nl = "Dit is de Nederlandse beschrijving"
        description_undetermined = "This is the default description"
        media_type = "text/plain"
        relationship = "external"
        ancestry = await self._load_partial(
            f"""
<sources>
    <source handle="_e2b5e77b4cc5c91c9ed60a6cb39" change="1558277217" id="S0000">
      <srcattribute type="betty:link-full:url" value="{url_undetermined}"/>
      <srcattribute type="betty:link-full:url:nl" value="{url_nl}"/>
      <srcattribute type="betty:link-full:label" value="{label_undetermined}"/>
      <srcattribute type="betty:link-full:label:nl" value="{label_nl}"/>
      <srcattribute type="betty:link-full:description" value="{description_undetermined}"/>
      <srcattribute type="betty:link-full:description:nl" value="{description_nl}"/>
      <srcattribute type="betty:link-full:media_type" value="{media_type}"/>
      <srcattribute type="betty:link-full:relationship" value="{relationship}"/>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert source.links
        link = source.links.view[0]
        localizer_nl = Localizer("nl", NullTranslations())
        assert link.url.localize(localizer_nl) == url_nl
        assert link.url.localize(DEFAULT_LOCALIZER) == url_undetermined
        assert link.label is not None
        assert link.label.localize(localizer_nl) == label_nl
        assert link.label.localize(DEFAULT_LOCALIZER) == label_undetermined
        assert link.description is not None
        assert link.description.localize(localizer_nl) == description_nl
        assert link.description.localize(DEFAULT_LOCALIZER) == description_undetermined
        assert link.media_type == MediaType(media_type)
        assert link.relationship == relationship

    async def test__load_attribute_links_should_warn_about_attribute_link_without_url(
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

    async def test__load_attribute_links_should_warn_about_attribute_link_invalid_media_type(
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
        link_one = source.links.view[0]
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

    async def test_event_should_include_privacy_from_element(self) -> None:
        ancestry = await self._load_partial(
            """
<events>
    <event handle="_e1dd3ac2fa22e6fefa18f738bdd" change="1552126811" id="E0000" priv="1">
        <type>Birth</type>
    </event>
</events>
"""
        )
        event = ancestry[Event]["E0000"]
        assert event.private

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

    async def _assert_file_should_include_path(
        self, expected: Path, file_src: Path, media_path: Path | None
    ) -> None:
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="{file_src}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
    </object>
</objects>
""",
            media_path=media_path,
        )
        file = ancestry[File]["O0000"]
        assert file.path == expected
        assert file.path.is_absolute()

    async def test_file_should_include_path_with_media_path_with_relative_file_path(
        self, tmp_path: Path
    ) -> None:
        media_path = tmp_path / "media"
        media_path.mkdir()
        file_path = Path("file.path")
        (media_path / file_path).touch()
        await self._assert_file_should_include_path(
            media_path / file_path, file_path, media_path
        )

    async def test_file_should_include_path_with_media_path_with_absolute_file_path(
        self, tmp_path: Path
    ) -> None:
        media_path = tmp_path / "media"
        file_path = tmp_path / "somewhere-outside-the-media-path" / "file.path"
        file_path.parent.mkdir()
        file_path.touch()
        await self._assert_file_should_include_path(file_path, file_path, media_path)

    async def test_file_should_include_path_without_media_path_with_relative_file_path(
        self,
    ) -> None:
        with pytest.raises(UserFacingGrampsError):
            await self._load_partial(
                f"""
    <objects>
        <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
            <file src="{Path("file.path")}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
        </object>
    </objects>
    """
            )

    async def test_file_should_include_path_without_media_path_with_absolute_file_path(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "somewhere-outside-the-media-path" / "file.path"
        file_path.parent.mkdir()
        file_path.touch()
        await self._assert_file_should_include_path(file_path, file_path, None)

    async def test_file_should_include_description(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="{file_path}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e" description="My First Description"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert file.description is not None
        assert file.description.localize(DEFAULT_LOCALIZER) == "My First Description"

    async def test_file_not_exists_should_error(self, tmp_path: Path) -> None:
        with pytest.raises(UserFacingGrampsError):
            await self._load_partial(
                f"""
    <objects>
        <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
            <file src="{tmp_path / "non-existent-file.path"}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
        </object>
    </objects>
    """
            )

    async def test_file_should_include_privacy_from_element(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000" priv="1">
        <file src="{file_path}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert file.private

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
        self, expected: Privacy, attribute_value: str, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="{file_path}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
        <attribute type="betty:privacy" value="{attribute_value}"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert expected == file.privacy

    async def test_file_should_include_note(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="{file_path}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
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
        note = list(file.notes)[0]
        assert note.id == "N0000"

    async def test_file_should_include_copyright_notice(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="{file_path}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
        <attribute type="betty:copyright-notice" value="public-domain"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert isinstance(file.copyright_notice, PublicDomainCopyrightNotice)

    async def test_file_should_ignore_unknown_copyright_notice(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="{file_path}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
        <attribute type="betty:copyright-notice" value="non-existent-copyright-notice"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert file.copyright_notice is None

    async def test_file_should_include_license(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="{file_path}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
        <attribute type="betty:license" value="public-domain"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert isinstance(file.license, PublicDomainLicense)

    async def test_file_should_ignore_unknown_license(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.path"
        file_path.touch()
        ancestry = await self._load_partial(
            f"""
<objects>
    <object handle="_e66f421249f3e9ebf6744d3b11d" change="1583534526" id="O0000">
        <file src="{file_path}" mime="text/plain" checksum="d41d8cd98f00b204e9800998ecf8427e"/>
        <attribute type="betty:license" value="non-existent-license"/>
    </object>
</objects>
"""
        )
        file = ancestry[File]["O0000"]
        assert file.license is None

    async def test_source_from_source_should_include_privacy_from_element(self) -> None:
        ancestry = await self._load_partial(
            """
<sources>
    <source handle="_e1dd686b04813540eb3503a342b" change="1558277217" id="S0000" priv="1">
        <stitle>A Whisper</stitle>
    </source>
</sources>
"""
        )
        source = ancestry[Source]["S0000"]
        assert source.private

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

    async def test_citation_should_include_privacy_from_element(self) -> None:
        ancestry = await self._load_partial(
            """
<citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0000" priv="1">
        <confidence>2</confidence>
        <sourceref hlink="_e1dd686b04813540eb3503a342b"/>
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
        assert citation.private

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

    async def test_note_should_include_privacy_from_element(self) -> None:
        ancestry = await self._load_partial(
            """
<notes>
    <note handle="_e1cb35d7e6c1984b0e8361e1aee" change="1551643112" id="N0000" type="Transcript" priv="1">
        <text>I left this for you.</text>
    </note>
</notes>
"""
        )
        note = ancestry[Note]["N0000"]
        assert note.private

    async def test_citation_should_include_location_from_page(self) -> None:
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
        assert citation.location is not None
        assert citation.location.localize(DEFAULT_LOCALIZER) == "My First Page"

    async def test_citation_should_include_source(self) -> None:
        ancestry = await self._load_partial(
            """
<citations>
    <citation handle="_e2c25a12a097a0b24bd9eae5090" change="1558277266" id="C0000">
        <confidence>2</confidence>
        <sourceref hlink="_e1dd686b04813540eb3503a342b"/>
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
        source = ancestry[Source]["S0000"]
        assert citation.source is source

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
            presence_role_mapping={"MyFirstRole": Subject},
        )
        person = ancestry[Person]["I0000"]
        presence = list(person.presences)[0]
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
        presence = list(person.presences)[0]
        assert presence.private

    async def test_url_should_include_path_as_url(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e21e77455147d79f6b4cc1c76a4" change="1553878037" id="I0000">
        <gender>U</gender>
        <url href="https://alexandria.example.com" type="Unknown"/>
    </person>
</people>
"""
        )
        links = ancestry[Person]["I0000"].links
        assert len(links) == 1
        link = list(links)[0]
        assert link.url.localize(DEFAULT_LOCALIZER) == "https://alexandria.example.com"

    async def test_url_should_include_description_as_label(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e21e77455147d79f6b4cc1c76a4" change="1553878037" id="I0000">
        <gender>U</gender>
        <url href="https://alexandria.example.com" type="Unknown" description="Library of Alexandria Catalogue"/>
    </person>
</people>
"""
        )
        links = ancestry[Person]["I0000"].links
        assert len(links) == 1
        link = list(links)[0]
        assert link.label is not None
        assert (
            link.label.localize(DEFAULT_LOCALIZER) == "Library of Alexandria Catalogue"
        )

    async def test_url_should_include_relationship(self) -> None:
        ancestry = await self._load_partial(
            """
<people>
    <person handle="_e21e77455147d79f6b4cc1c76a4" change="1553878037" id="I0000">
        <gender>U</gender>
        <url href="https://alexandria.example.com" type="Unknown" description="Library of Alexandria Catalogue"/>
    </person>
</people>
"""
        )
        links = ancestry[Person]["I0000"].links
        assert len(links) == 1
        link = list(links)[0]
        assert link.relationship == "external"

    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            (None, ""),
            (None, "nl_NL"),
            (Locale("nl"), "nl"),
            (Locale("nl", "NL"), "nl-NL"),
        ],
    )
    async def test_load_locale(
        self, expected: Locale | None, locale: str, isolated_app: App
    ) -> None:
        user = StaticUser()
        async with Project.new_isolated(isolated_app) as project, project:
            sut = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                user=user,
                copyright_notices=StaticPluginRepository(CopyrightNoticeDefinition),
                licenses=StaticPluginRepository(LicenseDefinition),
                genders=StaticPluginRepository(GenderDefinition),
                attribute_prefix_key=self.ATTRIBUTE_PREFIX_KEY,
            )
            assert await sut.load_locale(locale) == expected
        if expected is None:
            user.assert_message_warning(locale)
