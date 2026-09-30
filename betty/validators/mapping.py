"""
Mapping data validators.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, overload

from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.locator.operator import Key
from betty.validation import Invalid, group, locate

if TYPE_CHECKING:
    from betty.validation import Validator


@overload
def is_mapping(
    *, keys: None = None, value: None = None
) -> Pipeline[Any, Mapping[Any, Any]]:
    pass


@overload
def is_mapping[ValueT](
    *, keys: None = None, values: Validator[Any, ValueT]
) -> Pipeline[Any, Mapping[Any, ValueT]]:
    pass


@overload
def is_mapping[KeyT](
    *, keys: Validator[Any, KeyT], values: None
) -> Pipeline[Any, Mapping[KeyT, Any]]:
    pass


@overload
def is_mapping[ValueT, KeyT](
    *,
    keys: Validator[Any, KeyT],
    values: Validator[Any, ValueT],
) -> Pipeline[Any, Mapping[KeyT, ValueT]]:
    pass


def is_mapping[ValueT, KeyT](values=None, keys=None, /):
    """
    Validate that a value is a key-value mapping.

    Optionally validate that keys and/or values are of a given type.
    """

    @group()
    def _is_mapping(value: Any, /) -> Mapping[KeyT, ValueT]:
        if not isinstance(value, Mapping):
            raise Invalid(_("This must be a key-value mapping."))
        if values is None and keys is None:
            return value
        validated_mapping = {}
        for item_key, item_value in value.items():
            validated_key = item_key
            validated_value = item_value
            if keys or values:
                with locate(Key(str(item_key))):
                    if keys:
                        validated_key = keys(item_key)
                    if values:
                        validated_value = values(item_value)
            validated_mapping[validated_key] = validated_value
        return validated_mapping

    return Pipeline(_is_mapping)
