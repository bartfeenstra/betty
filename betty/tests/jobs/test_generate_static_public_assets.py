from betty.jobs.generate_static_public_assets import GenerateStaticPublicAssets
from betty.project import ProjectLocale
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.jinja import assert_betty_html
from betty.test_utils.job import do


class TestGenerateStaticPublicAssets:
    async def test_do(self, isolated_project_factory: IsolatedProjectFactory) -> None:
        async with isolated_project_factory(
            locales=[
                ProjectLocale(
                    "nl-NL",
                    alias="nl",
                ),
                ProjectLocale(
                    "en-US",
                    alias="en",
                ),
            ],
        ) as project:
            await do(GenerateStaticPublicAssets(project=project))

            with open(
                await assert_betty_html(project, "/index.html"), encoding="utf-8"
            ) as f:
                meta_redirect = (
                    '<meta http-equiv="refresh" content="0; url=/nl/index.html">'
                )
                assert meta_redirect in f.read()
