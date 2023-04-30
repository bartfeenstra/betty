import sys

from betty.app import App
from betty.gui import BettyApplication
from betty.gui.app import WelcomeWindow

if __name__ == "__main__":
    with App() as app:
        qapp = BettyApplication([sys.argv[0]], app=app)
        window = WelcomeWindow(app)
        window.show()
        sys.exit(qapp.exec())
