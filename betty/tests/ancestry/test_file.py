from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, cast

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.ancestry.source import Source
from betty.copyright_notice.copyright_notices import (
    PublicDomain as PublicDomainCopyrightNotice,
)
from betty.license.licenses import PublicDomain as PublicDomainLicense
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.media_type.media_types import PLAIN_TEXT
from betty.model import Entity
from betty.privacy import Privacy
from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.model import EntityDefinitionTestBase, EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.plugin import PluginDefinition

import pytest


class TestFileDefinition(EntityDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return File.plugin()


class TestFile(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            File(Path(__file__)),
            File(Path(__file__), description="My First File"),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    async def test_id(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.id == file_id

    async def test_name__with_name(self, tmp_path: Path) -> None:
        name = "a-file.a-suffix"
        sut = File(
            tmp_path / "file",
            name=name,
        )
        assert sut.name == name

    async def test_private(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_media_type(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.media_type is None
        media_type = PLAIN_TEXT
        sut.media_type = media_type
        assert sut.media_type == media_type

    async def test_path__with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = "BETTY01"
            file_path = Path(f.name)
            sut = File(
                id=file_id,
                path=file_path,
            )
            assert sut.path == file_path

    async def test_path__with_str(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = "BETTY01"
            sut = File(
                id=file_id,
                path=Path(f.name),
            )
            assert sut.path == Path(f.name)

    async def test_description(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert not sut.description
        description = "Hi, my name is Betty!"
        sut.description = description
        assert sut.description is not None
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_notes(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert list(sut.notes) == []
        notes = [Note(DUMMY_LOCALIZABLE), Note(DUMMY_LOCALIZABLE)]
        sut.notes = notes
        assert list(sut.notes) == notes

    async def test_referees(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert list(sut.referees) == []

        entity_one = DummyHasFileReferences()
        entity_two = DummyHasFileReferences()
        FileReference(entity_one, sut)
        FileReference(entity_two, sut)
        assert [file_reference.referee for file_reference in sut.referees] == [
            entity_one,
            entity_two,
        ]

    async def test_citations(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert list(sut.citations) == []

    async def test_dump_linked_data__should_dump_minimal(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
            )
            expected: Mapping[str, Any] = {
                "@context": {"description": "https://schema.org/description"},
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": False,
                "citations": [],
                "notes": [],
                "links": [],
                "referees": [],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

    async def test_dump_linked_data__should_dump_full(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
                media_type=PLAIN_TEXT,
                copyright_notice=PublicDomainCopyrightNotice(),
                license=PublicDomainLicense(),
                description="The Description",
            )
            file.notes.add(
                Note(
                    id="the_note",
                    text="The Note",
                )
            )
            reference = FileReference(Person(id="the_person"), file)
            file.citations.add(
                Citation(
                    id="the_citation",
                    source=Source(
                        id="the_source",
                        name="The Source",
                    ),
                )
            )
            expected: Mapping[str, Any] = {
                "@context": {"description": "https://schema.org/description"},
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": False,
                "mediaType": "text/plain",
                "citations": [
                    "/citation/the_citation/index.json",
                ],
                "notes": [
                    "/note/the_note/index.json",
                ],
                "links": [],
                "referees": [
                    {
                        "id": reference.id,
                        "referee": "/person/the_person/index.json",
                        "file": "/file/the_file/index.json",
                    },
                ],
                "description": {DEFAULT_LOCALE_TAG: "The Description"},
                "copyrightNotice": "public-domain",
                "license": "public-domain",
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

    async def test_dump_linked_data__should_dump_private(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
                privacy=Privacy.PRIVATE,
                media_type=PLAIN_TEXT,
                description="The File",
            )
            file.notes.add(
                Note(
                    id="the_note",
                    text="The Note",
                )
            )
            reference = FileReference(Person(id="the_person"), file)
            file.citations.add(
                Citation(
                    id="the_citation",
                    source=Source(
                        id="the_source",
                        name="The Source",
                    ),
                )
            )
            expected: Mapping[str, Any] = {
                "@context": {"description": "https://schema.org/description"},
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": True,
                "citations": [
                    "/citation/the_citation/index.json",
                ],
                "notes": [
                    "/note/the_note/index.json",
                ],
                "links": [],
                "referees": [
                    {
                        "id": reference.id,
                        "referee": "/person/the_person/index.json",
                        "file": "/file/the_file/index.json",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

    def test_get_mutables(self) -> None:
        copyright_notice = PublicDomainCopyrightNotice()
        license = PublicDomainLicense()  # noqa A001
        sut = File(Path(__file__), copyright_notice=copyright_notice, license=license)
        sut.immutable = True
        assert copyright_notice.immutable
        assert license.immutable
