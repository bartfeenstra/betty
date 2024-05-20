import sys
from asyncio import run

from betty.app import App
from betty.gui import BettyApplication
from betty.gui.app import WelcomeWindow


def main() -> None:
    """
    Launch Betty for PyInstaller builds.
    """
    run(_main())


async def _main() -> None:
    async with App.new_from_environment() as app, BettyApplication(
        [sys.argv[0]]
    ).with_app(app) as qapp:
        window = WelcomeWindow(app)
        window.show()
        sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
