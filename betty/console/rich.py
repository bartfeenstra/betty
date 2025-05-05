"""
Rich integration for Betty's console.
"""

from rich.style import Style
from rich.theme import Theme


class ConsoleTheme(Theme):
    """
    A Rich theme for Betty's console.
    """

    def __init__(self):
        super().__init__(
            {
                "prompt": Style(color="bright_magenta", bold=True),
            }
        )
