from __future__ import annotations

from typing import TYPE_CHECKING, Union, Any, Callable

from betty.config.load import ConfigurationValidationError

try:
    from typing_extensions import TypeAlias
except ModuleNotFoundError:
    from typing import TypeAlias  # type: ignore

if TYPE_CHECKING:
    from betty.builtins import _


Instance: TypeAlias = Any
Value: TypeAlias = Any
Validator: TypeAlias = Callable[[Instance, Value], Value]


def validate_positive_number(__, value: Union[int, float]) -> Union[int, float]:
    if value <= 0:
        raise ConfigurationValidationError(_('This must be a positive number.'))
    return value


def validate(*validators: Validator) -> Callable[[Callable], Callable[[Instance, Value], None]]:
    def build_validated_setter(f: Callable) -> Callable[[Instance, Value], None]:
        def validated_setter(instance: Instance, value: Value) -> None:
            for validator in validators:
                value = validator(instance, value)
            f(instance, value)
        validated_setter._betty_configuration_validators = validators  # type: ignore
        return validated_setter
    return build_validated_setter
