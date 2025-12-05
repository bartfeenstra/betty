"""
Rich integration.
"""

from rich.style import Style
from rich.theme import Theme as RichTheme


class Theme(RichTheme):
    """
    A Rich theme for Betty's console.
    """

    def __init__(self):
        super().__init__(
            {
                "prompt": Style(color="bright_magenta", bold=True),
            }
        )
