"""
Provide text widgets for the Graphical User Interface.
"""

from typing import final

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel
from typing_extensions import override


class Text(QLabel):
    def __init__(self, text: str | None = None):
        super().__init__()
        if text:
            self.setText(text)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByKeyboard
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.setOpenExternalLinks(True)


@final
class Caption(Text):
    def __init__(self, text: str | None = None):
        super().__init__(text)
        font = QFont()
        self.setFont(font)


@final
class Code(Text):
    def __init__(self, text: str | None = None):
        super().__init__(text)
        font = QFont()
        self.setFont(font)

    @override
    def setText(self, a0: str | None) -> None:
        super().setText(f"<pre>{a0}</pre>" if a0 else a0)
