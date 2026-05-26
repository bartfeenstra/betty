"""
Mapping data assertions.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any, overload

from betty.assertions.type import assert_type
from betty.exception import reraise_with_indicator
from betty.functools import Pipe, Pipeline
from betty.indicator.selector import Key


@overload
def assert_mapping(
    value_assertion: None = None, key_assertion: None = None, /
) -> Pipeline[Any, MutableMapping[Any, Any]]:
    pass


@overload
def assert_mapping[ReturnT](
    value_assertion: Pipe[Any, ReturnT], key_assertion: None = None, /
) -> Pipeline[Any, MutableMapping[Any, ReturnT]]:
    pass


@overload
def assert_mapping[AssertionKeyT](
    value_assertion: None, key_assertion: Pipe[Any, AssertionKeyT], /
) -> Pipeline[Any, MutableMapping[AssertionKeyT, Any]]:
    pass


@overload
def assert_mapping[ReturnT, AssertionKeyT](
    value_assertion: Pipe[Any, ReturnT],
    key_assertion: Pipe[Any, AssertionKeyT],
    /,
) -> Pipeline[Any, MutableMapping[AssertionKeyT, ReturnT]]:
    pass


def assert_mapping[ReturnT, AssertionKeyT](
    value_assertion: Pipe[Any, ReturnT] | None = None,
    key_assertion: Pipe[Any, AssertionKeyT] | None = None,
    /,
):
    """
    Assert that a value is a key-value mapping.

    Optionally assert that keys and/or values are of a given type.
    """

    def _assert_mapping(value: Any, /) -> MutableMapping[AssertionKeyT, ReturnT]:
        mapping = assert_type(Mapping)(value)
        if value_assertion is None and key_assertion is None:
            return dict(mapping)
        asserted_mapping = {}
        for value_key, value_value in mapping.items():
            asserted_value_key = value_key
            if key_assertion:
                with reraise_with_indicator(Key(str(value_key))):
                    asserted_value_key = key_assertion(value_key)
            asserted_value_value = value_value
            if value_assertion:
                with reraise_with_indicator(Key(str(value_key))):
                    asserted_value_value = value_assertion(value_value)
            asserted_mapping[asserted_value_key] = asserted_value_value
        return asserted_mapping

    return Pipeline(_assert_mapping)
