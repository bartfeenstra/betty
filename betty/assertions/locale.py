"""
Locale assertions.
"""

from __future__ import annotations

from betty.assertions.if_else import assert_if_else
from betty.assertions.none import assert_none
from betty.assertions.str import assert_str
from betty.locale import from_language_tag

assert_locale = assert_str() | from_language_tag
"""
Assert that a value is a valid `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_.
"""


assert_optional_locale = assert_if_else(assert_none, assert_locale)
"""
Assert that a value is a valid `IETF BCP 47 language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_, or ``None``.
"""
