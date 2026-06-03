from json import dumps
from pathlib import Path

from betty.file import write
from betty.project import ProjectData
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
            configuration = ProjectData(title="Betty", url="https://example.com")
            await write(
                tmp_path / "betty.json",
                dumps(configuration.data().porter.dump(configuration)),
            )
            result = await run(app, "about", "--project", str(tmp_path / "betty.json"))
            assert "Betty" in result.stdout
