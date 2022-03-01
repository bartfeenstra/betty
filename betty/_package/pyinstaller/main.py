import sys

from betty.gui import BettyApplication, _WelcomeWindow

if __name__ == "__main__":
    app = BettyApplication([sys.argv[0]])
    window = _WelcomeWindow()
    window.show()
    sys.exit(app.exec())
