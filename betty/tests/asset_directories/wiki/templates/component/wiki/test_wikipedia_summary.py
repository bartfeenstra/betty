from betty.asset_directories import wiki
from betty.copyright_notices.wikipedia_contributors import WikipediaContributors
from betty.localizer import default_localizer
from betty.project import Project
from betty.test_utils.conftest import AssertJinja
from betty.wiki.client import Summary


async def test(assert_jinja_file: AssertJinja) -> None:
    summary = Summary("en", "Amsterdam", "Amstelredam", "Capital of the Netherlands")
    copyright_notice = WikipediaContributors("https://example.com")
    Project.asset_directories.add_init_plugins(assert_jinja_file.project, wiki)
    async with assert_jinja_file(
        "component/wiki/wikipedia-summary.html.j2",
        data={
            "wikipedia_summary": summary,
            "wikipedia_summary_copyright_notice": copyright_notice,
        },
    ) as rendered:
        assert summary.content in rendered
        assert default_localizer.localize(copyright_notice.summary) in rendered
        assert default_localizer.localize(copyright_notice.url) in rendered
