"""
Provide localizable assertions.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from betty.assertion import (
    AssertionChain,
    assert_or,
    assert_str,
    assert_mapping,
    assert_locale,
)
from betty.locale import UNDETERMINED_LOCALE

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from betty.locale.localizable import StaticTranslations


def assert_static_translations() -> (
    AssertionChain[Any, StaticTranslations & MutableMapping[str, str]]
):
    """
    Assert that a value represents static translations.
    """
    return assert_or(
        assert_str().chain(lambda translation: {UNDETERMINED_LOCALE: translation}),
        assert_mapping(assert_str(), assert_locale()),
    )
