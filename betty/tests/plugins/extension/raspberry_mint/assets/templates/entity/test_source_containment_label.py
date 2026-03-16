from betty.plugins.entity.source import Source
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja import assert_template_string


async def test_minimal() -> None:
    source = Source()
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>'
    async with assert_template_string(
        "{% include 'entity/source-containment-label.html.j2' %}",
        data={
            "source": source,
        },
        extensions={RaspberryMint},
    ) as (actual, _):
        assert actual == expected


async def test_with_contained_by() -> None:
    contained_by_contained_by_source = Source()
    contained_by_source = Source(contained_by=contained_by_contained_by_source)
    source = Source(contained_by=contained_by_source)
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>, <span lang="und" dir="auto">Source {contained_by_source.id}</span>, <span lang="und" dir="auto">Source {contained_by_contained_by_source.id}</span>'
    async with assert_template_string(
        "{% include 'entity/source-containment-label.html.j2' %}",
        data={
            "source": source,
        },
        extensions={RaspberryMint},
    ) as (actual, _):
        assert actual == expected


async def test_with_source_context() -> None:
    contained_by_source = Source()
    source = Source(contained_by=contained_by_source)
    expected = f'<span lang="und" dir="auto">Source {source.id}</span>'
    async with assert_template_string(
        "{% include 'entity/source-containment-label.html.j2' %}",
        data={
            "source": source,
            "source_context": contained_by_source,
        },
        extensions={RaspberryMint},
    ) as (actual, _):
        assert actual == expected
