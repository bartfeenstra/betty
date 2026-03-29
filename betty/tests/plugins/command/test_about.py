from pathlib import Path

from betty.portable.file import dump_file
from betty.project.data import ProjectConfiguration
from betty.rich.user import RichUser
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.console import run


class TestAbout:
    async def test_configure(self, isolated_app_factory: IsolatedAppFactory) -> None:
        async with isolated_app_factory(user=RichUser()) as app:
            result = await run(app, "about")
            assert "Betty" in result.stdout

    async def test_configure__with_project(
        self, isolated_app_factory: IsolatedAppFactory, tmp_path: Path
    ) -> None:
        async with isolated_app_factory(user=RichUser()) as app:
            configuration = ProjectConfiguration(
                title="Betty", url="https://example.com"
            )
            await dump_file(
                configuration.data().porter.dump(configuration), tmp_path / "betty.json"
            )
            result = await run(app, "about", "--project", str(tmp_path / "betty.json"))
            assert "Betty" in result.stdout
