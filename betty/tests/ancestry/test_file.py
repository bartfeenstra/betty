from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Sequence, Mapping, Any, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.note import Note
from betty.ancestry.person import Person
from betty.privacy import Privacy
from betty.ancestry.source import Source
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.media_type.media_types import PLAIN_TEXT
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import EntityTestBase
from betty.tests.ancestry.test___init__ import DummyHasFileReferences

if TYPE_CHECKING:
    from betty.model import Entity


class TestFile(EntityTestBase):
    @override
    def get_sut_class(self) -> type[File]:
        return File

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            File(Path(__file__)),
            File(Path(__file__), description="My First File"),
        ]

    async def test_id(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert sut.id == file_id

    async def test_name_with_name(self, tmp_path: Path) -> None:
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

    async def test_path_with_path(self) -> None:
        with NamedTemporaryFile() as f:
            file_id = "BETTY01"
            file_path = Path(f.name)
            sut = File(
                id=file_id,
                path=file_path,
            )
            assert sut.path == file_path

    async def test_path_with_str(self) -> None:
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
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_notes(self) -> None:
        file_id = "BETTY01"
        file_path = Path("~")
        sut = File(
            id=file_id,
            path=file_path,
        )
        assert list(sut.notes) == []
        notes = [Note(text=""), Note(text="")]
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

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
            )
            expected: Mapping[str, Any] = {
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": False,
                "entities": [],
                "citations": [],
                "notes": [],
                "links": [
                    {
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                        "locale": "und",
                    },
                    {
                        "url": "/file/the_file/index.html",
                        "relationship": "alternate",
                        "mediaType": "text/html",
                        "locale": "en-US",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
                media_type=PLAIN_TEXT,
            )
            file.notes.add(
                Note(
                    id="the_note",
                    text="The Note",
                )
            )
            FileReference(Person(id="the_person"), file)
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
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": False,
                "mediaType": "text/plain",
                "entities": [
                    "/person/the_person/index.json",
                ],
                "citations": [
                    "/citation/the_citation/index.json",
                ],
                "notes": [
                    "/note/the_note/index.json",
                ],
                "links": [
                    {
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                        "locale": "und",
                    },
                    {
                        "url": "/file/the_file/index.html",
                        "relationship": "alternate",
                        "mediaType": "text/html",
                        "locale": "en-US",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        with NamedTemporaryFile() as f:
            file = File(
                id="the_file",
                path=Path(f.name),
                private=True,
                media_type=PLAIN_TEXT,
            )
            file.notes.add(
                Note(
                    id="the_note",
                    text="The Note",
                )
            )
            FileReference(Person(id="the_person"), file)
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
                "@id": "https://example.com/file/the_file/index.json",
                "id": "the_file",
                "private": True,
                "entities": [
                    "/person/the_person/index.json",
                ],
                "citations": [
                    "/citation/the_citation/index.json",
                ],
                "notes": [
                    "/note/the_note/index.json",
                ],
                "links": [
                    {
                        "url": "/file/the_file/index.json",
                        "relationship": "canonical",
                        "mediaType": "application/ld+json",
                        "locale": "und",
                    },
                ],
            }
            actual = await assert_dumps_linked_data(file)
            assert actual == expected
