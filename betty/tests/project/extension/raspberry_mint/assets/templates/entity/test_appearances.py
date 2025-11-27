from pathlib import Path

from betty.ancestry.event import Event
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    expected = ""
    async with assert_template_file(
        data={
            "file_references": [],
        },
        extensions={RaspberryMint},
        template="entity/appearances.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_public_referees() -> None:
    referee = Event(id="E0")
    file = File(Path(__file__))
    file_reference = FileReference(referee, file)
    async with assert_template_file(
        data={
            "file_references": [file_reference],
        },
        extensions={RaspberryMint},
        template="entity/appearances.html.j2",
    ) as (actual, _):
        assert "#appearances" in actual
        assert f"/event/{referee.public_id}/index.html" in actual


async def test_without_public_referees() -> None:
    referee = Event(id="E0", private=True)
    file = File(Path(__file__))
    file_reference = FileReference(referee, file)
    expected = ""
    async with assert_template_file(
        data={
            "file_references": [file_reference],
        },
        extensions={RaspberryMint},
        template="entity/appearances.html.j2",
    ) as (actual, _):
        assert actual == expected
