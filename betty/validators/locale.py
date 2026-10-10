"""
Locale validators.
"""

from __future__ import annotations

from betty.locale import from_language_tag
from betty.validators.if_else import is_if_else
from betty.validators.none import is_none
from betty.validators.str import is_str

is_locale = is_str | from_language_tag
"""
Validate that a value is a valid `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_.
"""


is_optional_locale = is_if_else(is_none, is_locale)
"""
Validate that a value is a valid `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_, or ``None``.
"""
