from json import dumps
from pathlib import Path

from betty.file import write
from betty.project import ProjectData
from betty.test_utils.conftest import NewIsolatedApp
from betty.test_utils.console import run
from betty.uis.console import Console


class TestAbout:
    async def test_configure(self, new_isolated_app: NewIsolatedApp) -> None:
        async with new_isolated_app(ui=Console()) as app, app:
            result = await run(app, "about")
            assert "Betty" in result.stdout

    async def test_configure__with_project(
        self, new_isolated_app: NewIsolatedApp, tmp_path: Path
    ) -> None:
        async with new_isolated_app(ui=Console()) as app, app:
            configuration = ProjectData(title="Betty", url="https://example.com")
            await write(
                tmp_path / "betty.json",
                dumps(configuration.definition.porter.dump(configuration)),
            )
            result = await run(app, "about", "--project", str(tmp_path / "betty.json"))
            assert "Betty" in result.stdout
