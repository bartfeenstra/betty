from betty.jobs.generate_localized_public_assets import GenerateLocalizedPublicAssets
from betty.jobs.generate_static_public_assets import GenerateStaticPublicAssets
from betty.project import ProjectLocale
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.jinja import assert_betty_html
from betty.test_utils.job import do


class TestGenerateLocalizedPublicAssets:
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
            await do(
                GenerateStaticPublicAssets(project=project),
                GenerateLocalizedPublicAssets(project=project),
            )

            await assert_betty_html(project, "/nl/index.html")
            await assert_betty_html(project, "/en/index.html")
