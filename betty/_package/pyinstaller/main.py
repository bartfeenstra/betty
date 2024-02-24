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
    async with App() as app:
        qapp = BettyApplication([sys.argv[0]], app=app)
        window = WelcomeWindow(app)
        window.show()
        sys.exit(qapp.exec())

if __name__ == "__main__":
    main()
