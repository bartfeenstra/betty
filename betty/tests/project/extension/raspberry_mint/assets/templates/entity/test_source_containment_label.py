from betty.ancestry.source import Source
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateStringTestBase


class Test(TemplateStringTestBase):
    extensions = {RaspberryMint}

    async def test_minimal(self) -> None:
        source = Source()
        expected = f'<span lang="und" dir="auto">Source {source.id}</span>'
        async with self.assert_template_string(
            "{%- from 'entity/source-containment-label.html.j2' import source_containment_label -%}{{ source_containment_label(source) }}",
            data={
                "source": source,
            },
        ) as (actual, _):
            assert actual == expected

    async def test_with_contained_by(self) -> None:
        contained_by_contained_by_source = Source()
        contained_by_source = Source(contained_by=contained_by_contained_by_source)
        source = Source(contained_by=contained_by_source)
        expected = f'<span lang="und" dir="auto">Source {source.id}</span>, <span lang="und" dir="auto">Source {contained_by_source.id}</span>, <span lang="und" dir="auto">Source {contained_by_contained_by_source.id}</span>'
        async with self.assert_template_string(
            "{%- from 'entity/source-containment-label.html.j2' import source_containment_label -%}{{ source_containment_label(source) }}",
            data={
                "source": source,
            },
        ) as (actual, _):
            assert actual == expected

    async def test_with_source_context(self) -> None:
        contained_by_source = Source()
        source = Source(contained_by=contained_by_source)
        expected = f'<span lang="und" dir="auto">Source {source.id}</span>'
        async with self.assert_template_string(
            "{%- from 'entity/source-containment-label.html.j2' import source_containment_label -%}{{ source_containment_label(source, source_context) }}",
            data={
                "source": source,
                "source_context": contained_by_source,
            },
        ) as (actual, _):
            assert actual == expected
