from betty.ancestry.source import Source
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import assert_template_file


async def test_without_entities() -> None:
    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Source.plugin_id()}/index.html",
            "entity_type": Source,
            "entities": [],
        },
        extensions={CottonCandy},
        template="entity/page-list--source.html.j2",
    ) as (actual, _):
        assert "I'm sorry" in actual


async def test_with_public_entity() -> None:
    source = Source()

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Source.plugin_id()}/index.html",
            "entity_type": Source,
            "entities": [source],
        },
        extensions={CottonCandy},
        template="entity/page-list--source.html.j2",
    ) as (actual, _):
        assert source.id in actual


async def test_with_private_entity() -> None:
    source = Source(private=True)

    async with assert_template_file(
        data={
            "page_resource": f"betty:///{Source.plugin_id()}/index.html",
            "entity_type": Source,
            "entities": [source],
        },
        extensions={CottonCandy},
        template="entity/page-list--source.html.j2",
    ) as (actual, _):
        assert source.id not in actual
