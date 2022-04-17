import sys

from betty.app import App
from betty.gui import BettyApplication, _WelcomeWindow

if __name__ == "__main__":
    with App() as app:
        qapp = BettyApplication([sys.argv[0]])
        window = _WelcomeWindow(app)
        window.show()
        sys.exit(qapp.exec())
