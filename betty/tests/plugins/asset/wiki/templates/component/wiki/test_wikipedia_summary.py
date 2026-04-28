from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.asset_directory.wiki import WIKI
from betty.plugins.copyright_notice.wikipedia_contributors import WikipediaContributors
from betty.test_utils.conftest import AssertTemplateFile
from betty.wiki.client import Summary


async def test(assert_template_file: AssertTemplateFile) -> None:
    summary = Summary("en", "Amsterdam", "Amstelredam", "Capital of the Netherlands")
    copyright_notice = WikipediaContributors("https://example.com")
    async with assert_template_file(
        data={
            "wikipedia_summary": summary,
            "wikipedia_summary_copyright_notice": copyright_notice,
        },
        assets={WIKI},
        template="component/wiki/wikipedia-summary.html.j2",
    ) as (actual, _project):
        assert summary.content in actual
        assert copyright_notice.summary.localize(DEFAULT_LOCALIZER) in actual
        assert copyright_notice.url is not None
        assert copyright_notice.url.localize(DEFAULT_LOCALIZER) in actual
