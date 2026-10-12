from betty.jobs.generate_localized_public_assets import GenerateLocalizedPublicAssets
from betty.jobs.generate_static_public_assets import GenerateStaticPublicAssets
from betty.project import ProjectLocale
from betty.test_utils.conftest import NewIsolatedProject
from betty.test_utils.jinja import assert_betty_html
from betty.test_utils.job import do


class TestGenerateLocalizedPublicAssets:
    async def test_do(self, new_isolated_project: NewIsolatedProject) -> None:
        async with new_isolated_project() as project:
            project.locales = [
                ProjectLocale(
                    "nl-NL",
                    alias="nl",
                ),
                ProjectLocale(
                    "en-US",
                    alias="en",
                ),
            ]
            async with project:
                await do(
                    GenerateStaticPublicAssets(project=project),
                    GenerateLocalizedPublicAssets(project=project),
                )

                await assert_betty_html(project, "/nl/index.html")
                await assert_betty_html(project, "/en/index.html")
