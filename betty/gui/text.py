from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel


class Text(QLabel):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard | Qt.TextInteractionFlag.LinksAccessibleByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard | Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setOpenExternalLinks(True)


class Caption(Text):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        font = QFont()
        font.setPixelSize(12)
        self.setFont(font)
