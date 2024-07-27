"""
Provide localizable assertions.
"""

from typing import Any

from betty.assertion import (
    assert_or,
    assert_str,
    assert_mapping,
    assert_locale,
    AssertionChain,
)
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import StaticTranslations


def assert_static_translations() -> AssertionChain[Any, StaticTranslations]:
    """
    Assert that a value represents static translations.
    """
    return assert_or(
        assert_str().chain(lambda translation: {UNDETERMINED_LOCALE: translation}),
        assert_mapping(assert_str(), assert_locale()),
    )
