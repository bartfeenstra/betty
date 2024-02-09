"""
Provide text widgets for the Graphical User Interface.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel


class Text(QLabel):
    def __init__(self, text: str | None = None):
        super().__init__(text)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard | Qt.TextInteractionFlag.LinksAccessibleByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard | Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setOpenExternalLinks(True)


class Caption(Text):
    def __init__(self, text: str | None = None):
        super().__init__(text)
        font = QFont()
        self.setFont(font)


class Code(Text):
    def __init__(self, text: str | None = None):
        super().__init__()
        if text:
            self.setText(text)
        font = QFont()
        self.setFont(font)

    def setText(self, a0: str | None) -> None:
        super().setText(f'<pre>{a0}</pre>' if a0 else a0)
