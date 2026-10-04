"""
String data validators.
"""

from __future__ import annotations

from functools import partial
from typing import Any, final, overload, override

from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.validation import Invalid, group


@group()
def _is_str(
    value: Any,
    /,
    *,
    len_: int | None = None,
    min_len: int | None = None,
    max_len: int | None = None,
) -> str:
    if not isinstance(value, str):
        raise Invalid(_("This must be a string."))
    actual_len = len(value)
    if len_ is not None and actual_len != len_:
        raise Invalid(
            _("This must be {length} characters long.").format(length=str(len_))
        )
    if min_len is not None and actual_len < min_len:
        raise Invalid(
            _("This must be at least {length} characters long.").format(
                length=str(min_len)
            )
        )
    if max_len is not None and actual_len > max_len:
        raise Invalid(
            _("This must be at most {length} characters long.").format(
                length=str(max_len)
            )
        )
    return value


@final
class _IsStr(Pipeline[Any, str]):
    def __init__(self):
        super().__init__(_is_str)

    @overload
    def __call__(
        self,
        value: Any,
        /,
        *,
        len: int | None = None,
        min_len: int | None = None,
        max_len: int | None = None,
    ) -> str:
        pass

    @overload
    def __call__(
        self,
        *,
        len: int | None = None,
        min_len: int | None = None,
        max_len: int | None = None,
    ) -> Pipeline[Any, str]:
        pass

    @override
    def __call__(self, *value_, **kwargs):
        if value_:
            return _is_str(value_[0], **kwargs)
        return Pipeline(partial(_is_str, **kwargs))


is_str = _IsStr()
"""
Validate that a value is a Python ``str``.
"""
