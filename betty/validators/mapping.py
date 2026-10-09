"""
Mapping data validators.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from typing import TYPE_CHECKING, Any, final, overload, override

from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.operator import Key
from betty.validation import collect
from betty.validators import _StaticInvalid
from betty.validators.always import is_always_valid

if TYPE_CHECKING:
    from betty.validation import Validator


@final
class NotAMapping(_StaticInvalid):
    """
    Raised when a value is not a mapping.
    """

    _message = _("This must be a key-value mapping.")


def _is_mapping[KeyT, ValueT](
    value: Any,
    /,
    *,
    keys: Validator[Any, KeyT] = is_always_valid,
    values: Validator[Any, ValueT] = is_always_valid,
) -> Mapping[KeyT, ValueT]:
    if not isinstance(value, Mapping):
        raise NotAMapping(value)
    if values is is_always_valid and keys is is_always_valid:
        return value
    with collect(value) as errors:
        if keys is is_always_valid:
            value_keys = value.keys()
        else:
            value_keys = []
            for value_key in value:
                with errors.catch():
                    value_keys.append(keys(value_key))
        if values is is_always_valid:
            value_values = value.values()
        else:
            value_values = []
            for value_key, value_value in value.items():
                with (
                    errors.collect(
                        value_value, location=[Key(value_key)]
                    ) as value_errors,
                    value_errors.catch(),
                ):
                    value_values.append(values(value_value))
        return dict(zip(value_keys, value_values, strict=False))


@final
class _IsMapping(Pipe[Any, Mapping[Any, Any]]):
    def __init__(self):
        super().__init__(_is_mapping)

    @overload
    def __call__[KeyT, ValueT](
        self,
        value: Any,
        /,
        *,
        keys: Validator[Any, KeyT] = is_always_valid,
        values: Validator[Any, ValueT] = is_always_valid,
    ) -> Mapping[KeyT, ValueT]:
        pass

    @overload
    def __call__[KeyT, ValueT](
        self,
        *,
        keys: Validator[Any, KeyT] = is_always_valid,
        values: Validator[Any, ValueT] = is_always_valid,
    ) -> Pipe[Any, Mapping[KeyT, ValueT]]:
        pass

    @override
    def __call__(self, *value_, keys=is_always_valid, values=is_always_valid):
        if value_:
            return _is_mapping(value_[0], keys=keys, values=values)
        return Pipe(partial(_is_mapping, keys=keys, values=values))


is_mapping = _IsMapping()
"""
Validate that a value is a mapping.

Optionally validate that keys and/or values are of a given type.
"""
