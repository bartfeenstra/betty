from betty.portable.file import dump_file
from betty.project import Project
from betty.rich.user import RichUser
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.console import run


class TestAbout:
    async def test_configure(self, isolated_app_factory: IsolatedAppFactory) -> None:
        async with isolated_app_factory(user=RichUser()) as app, app:
            result = await run(app, "about")
            assert "Betty" in result.stdout

    async def test_configure__with_project(
        self, isolated_app_factory: IsolatedAppFactory
    ) -> None:
        async with (
            isolated_app_factory(user=RichUser()) as app,
            app,
            Project.new_isolated(app) as project,
        ):
            await dump_file(
                project.configuration.data().porter.dump(project.configuration),
                project.configuration_file,
            )
            result = await run(
                app,
                "about",
                "--project",
                str(project.configuration_file),
            )
            assert "Betty" in result.stdout
