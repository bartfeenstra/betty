from pathlib import Path

from betty.ancestry.event import Event
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/appearances.html.j2"

    async def test_minimal(self) -> None:
        expected = ""
        async with self.assert_template_file(
            data={"file_references": [], "page_resource": "betty:///sut.html"}
        ) as (actual, _):
            assert actual == expected

    async def test_with_public_referees(self) -> None:
        referee = Event(id="E0")
        file = File(Path(__file__))
        file_reference = FileReference(referee, file)
        async with self.assert_template_file(
            data={
                "file_references": [file_reference],
                "page_resource": "betty:///sut.html",
            }
        ) as (actual, _):
            assert "/sut.html#appearances" in actual
            assert "/event/E0/index.html" in actual

    async def test_without_public_referees(self) -> None:
        referee = Event(id="E0", private=True)
        file = File(Path(__file__))
        file_reference = FileReference(referee, file)
        expected = ""
        async with self.assert_template_file(
            data={
                "file_references": [file_reference],
                "page_resource": "betty:///sut.html",
            }
        ) as (actual, _):
            assert actual == expected
