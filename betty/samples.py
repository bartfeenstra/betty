"""
Samples of various things.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from betty.localizables.gettext import pgettext

if TYPE_CHECKING:
    from betty.localizable import Localizable

color_hex: Final[str] = "ff0000"
language_tag: Final[Localizable] = pgettext("sample-language-tag", "en-US")
