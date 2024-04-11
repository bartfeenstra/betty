import sys

from betty.app import App
from betty.asyncio import sync
from betty.gui import BettyApplication
from betty.gui.app import WelcomeWindow


@sync
async def main() -> None:
    """
    Launch Betty for PyInstaller builds.
    """
    async with App.new_from_environment() as app:
        async with BettyApplication([sys.argv[0]]).with_app(app) as qapp:
            window = WelcomeWindow(app)
            window.show()
            sys.exit(qapp.exec())

if __name__ == "__main__":
    main()
