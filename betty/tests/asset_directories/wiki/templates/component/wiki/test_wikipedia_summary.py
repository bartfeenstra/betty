from betty.asset_directories.wiki import wiki
from betty.copyright_notices.wikipedia_contributors import WikipediaContributors
from betty.localizer import default_localizer
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
        assets={wiki},
        template="component/wiki/wikipedia-summary.html.j2",
    ) as (actual, _project):
        assert summary.content in actual
        assert copyright_notice.summary.localize(default_localizer) in actual
        assert copyright_notice.url is not None
        assert copyright_notice.url.localize(default_localizer) in actual
