"""
Provide localizable assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.assertion import (
    AssertionChain,
    assert_locale_identifier,
    assert_mapping,
    assert_or,
    assert_str,
)
from betty.locale import UNDETERMINED_LOCALE

if TYPE_CHECKING:
    from betty.locale.localizable import StaticTranslationsMapping


def assert_static_translations() -> AssertionChain[Any, StaticTranslationsMapping]:
    """
    Assert that a value represents static translations.
    """
    return assert_or(
        assert_str().chain(lambda translation: {UNDETERMINED_LOCALE: translation}),
        assert_mapping(assert_str(), assert_locale_identifier()),
    )
