from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    url = "https://example.com/per/ma.link"
    async with assert_template_file(
        data={
            "url": url,
        },
        assets={raspberry_mint},
        template="component/permalink.html.j2",
    ) as (actual, _):
        assert "<a " in actual
        assert url in actual
