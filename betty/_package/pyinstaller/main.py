import sys
from asyncio import run
from pathlib import Path

from aiofiles.tempfile import TemporaryDirectory

from betty.app import App
from betty.gui import BettyApplication
from betty.gui.app import WelcomeWindow
from betty.project import Project, ProjectConfiguration


def main() -> None:
    """
    Launch Betty for PyInstaller builds.
    """
    run(_main())


async def _main() -> None:
    async with TemporaryDirectory() as project_configuration_directory_path_str:
        async with App.new_from_environment(
            Project(
                configuration=ProjectConfiguration(
                    configuration_file_path=Path(
                        project_configuration_directory_path_str
                    )
                    / "betty.json"
                )
            )
        ) as app:
            async with BettyApplication([sys.argv[0]]).with_app(app) as qapp:
                window = WelcomeWindow(app)
                window.show()
                sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
