from __future__ import annotations

from typing import TYPE_CHECKING, Union, Any, Callable

from betty.config.load import ConfigurationValidationError

try:
    from typing_extensions import TypeAlias
except ModuleNotFoundError:  # pragma: no cover
    from typing import TypeAlias  # type: ignore  # pragma: no cover

if TYPE_CHECKING:
    from betty.builtins import _


Instance: TypeAlias = Any
Value: TypeAlias = Any
Validator: TypeAlias = Callable[[Instance, Value], Value]


def validate_positive_number(value: Union[int, float]) -> Union[int, float]:
    if value <= 0:
        raise ConfigurationValidationError(_('This must be a positive number.'))
    return value
