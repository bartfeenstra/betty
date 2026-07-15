from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.enclosure import Enclosure
from betty.entities.place import Place
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    place = Place()
    expected = f'<span lang="und" dir="auto">Place {place.id}</span>'
    async with assert_template_file(
        "entity/place-enclosure-label.html.j2",
        data={
            "place": place,
        },
        assets={raspberry_mint},
    ) as (actual, _):
        assert actual == expected


async def test_with_enclosed_by(assert_template_file: AssertTemplateFile) -> None:
    enclosed_by_enclosed_by = Place()
    enclosed_by = Place()
    Enclosure(enclosed_by=enclosed_by_enclosed_by, encloses=enclosed_by)
    encloses = Place()
    Enclosure(encloses=encloses, enclosed_by=enclosed_by)
    expected = f'<span lang="und" dir="auto">Place {encloses.id}</span>, <span lang="und" dir="auto">Place {enclosed_by.id}</span>, <span lang="und" dir="auto">Place {enclosed_by_enclosed_by.id}</span>'
    async with assert_template_file(
        "entity/place-enclosure-label.html.j2",
        data={
            "place": encloses,
        },
        assets={raspberry_mint},
    ) as (actual, _):
        assert actual == expected


async def test_with_place_context(assert_template_file: AssertTemplateFile) -> None:
    enclosed_by = Place()
    encloses = Place()
    Enclosure(enclosed_by=enclosed_by, encloses=encloses)
    expected = f'<span lang="und" dir="auto">Place {encloses.id}</span>'
    async with assert_template_file(
        "entity/place-enclosure-label.html.j2",
        data={
            "place": encloses,
            "place_context": enclosed_by,
        },
        assets={raspberry_mint},
    ) as (actual, _):
        assert actual == expected
