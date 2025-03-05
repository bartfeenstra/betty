from pathlib import Path

from betty.ancestry.file import File
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import assert_template_file


async def test_without_entities() -> None:
    async with assert_template_file(
        data={
            "page_resource": f"betty:///{File.plugin_id()}/index.html",
            "entity_type": File,
            "entities": [],
        },
        extensions={CottonCandy},
        template="entity/page-list--file.html.j2",
    ) as (actual, _):
        assert "I'm sorry" in actual


async def test_with_public_entity() -> None:
    file = File(path=Path())

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{File.plugin_id()}/index.html",
            "entity_type": File,
            "entities": [file],
        },
        extensions={CottonCandy},
        template="entity/page-list--file.html.j2",
    ) as (actual, _):
        assert file.id in actual


async def test_with_private_entity() -> None:
    file = File(path=Path(), private=True)

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{File.plugin_id()}/index.html",
            "entity_type": File,
            "entities": [file],
        },
        extensions={CottonCandy},
        template="entity/page-list--file.html.j2",
    ) as (actual, _):
        assert file.id not in actual
